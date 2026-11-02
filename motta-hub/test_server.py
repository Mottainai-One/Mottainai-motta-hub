import http.client
import hashlib
import os
import time
import json
import sqlite3
import tempfile
import threading
import unittest
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from server import create_server, get_overview, get_table, initialize_database, list_tables, read_connection, validated_script
from import_catalog import import_catalog, parse_catalog, read_xlsx


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "test.sqlite3"
        initialize_database(self.database)

    def test_seed_and_restart_preserve_data(self):
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM catalog_tables").fetchone()[0], 48)
            self.assertEqual(connection.execute("SELECT count(*) FROM table_columns").fetchone()[0], 336)
            connection.execute("UPDATE catalog_tables SET description = 'preservada' WHERE id = 'table-1-1'")
            connection.commit()
        initialize_database(self.database)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(len(list_tables(connection, "")), 48)
            self.assertEqual(get_table(connection, "table-1-1")["description"], "preservada")

    def test_server_pins_relative_database_path(self):
        import os
        relative = Path(os.path.relpath(self.database, Path.cwd()))
        with create_server(relative, 0) as server:
            self.assertEqual(server.database, self.database.resolve())
            self.assertTrue(server.database.is_absolute())

    def test_empty_catalog_is_not_reseeded_on_restart(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('PRAGMA foreign_keys = ON')
            connection.execute('DELETE FROM catalog_tables')
        for _ in range(2):
            initialize_database(self.database)
            with closing(read_connection(self.database)) as connection:
                self.assertEqual(list_tables(connection, ''), [])
                self.assertEqual(connection.execute('SELECT count(*) FROM table_columns').fetchone()[0], 0)
                self.assertEqual(connection.execute('SELECT count(*) FROM users').fetchone()[0], 3)

    def test_relation_uniqueness_and_position_constraints(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            invalid = [
                ("missing", "test", "", 0),
                ("table-1-1", "record_id", "", 7),
                ("table-1-1", "another", "", 0),
                ("table-1-1", "another", "", -1),
            ]
            for values in invalid:
                with self.subTest(values=values), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)", values)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO catalog_tables(id,schema_name,name) SELECT 'duplicate',schema_name,name FROM catalog_tables WHERE id='table-1-1'")

    def test_search_normalization_literal_characters_and_order(self):
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(len(list_tables(connection, "  STÁTEMENTS  ")), 1)
            self.assertEqual(len(list_tables(connection, "demo_home")), 8)
            self.assertEqual(list_tables(connection, "%"), [])
            self.assertEqual(list_tables(connection, "' OR 1=1 --"), [])
            columns = get_table(connection, "table-1-1")["columns"]
            self.assertEqual(columns[0]["name"], "record_id")
            self.assertEqual(columns[-1]["name"], "updated_at")
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM catalog_tables")

    def test_new_records_fit_schema_without_reseeding(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO catalog_tables VALUES ('test-extra','demo_test','new_table','')")
            connection.execute("INSERT INTO table_columns(table_id,name,description,position) VALUES ('test-extra','new_column','Nova descrição',0)")
            connection.commit()
        initialize_database(self.database)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(get_table(connection, "test-extra")["columns"][0]["description"], "Nova descrição")
            self.assertEqual(len(list_tables(connection, "")), 49)

    def test_v1_migration_preserves_catalog_and_is_idempotent(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DROP TABLE sessions')
            connection.execute('DROP TABLE users')
            connection.execute('PRAGMA user_version = 1')
            connection.execute("UPDATE catalog_tables SET description='migration preserved' WHERE id='table-1-1'")
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 4)
            self.assertEqual(connection.execute('SELECT count(*) FROM users').fetchone()[0], 3)
            self.assertEqual(connection.execute('SELECT count(*) FROM catalog_tables').fetchone()[0], 48)
            self.assertEqual(connection.execute('SELECT count(*) FROM table_columns').fetchone()[0], 336)
            self.assertEqual(get_table(connection,'table-1-1')['description'],'migration preserved')

    def test_incompatible_database_is_not_overwritten(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA user_version = 3")
        with self.assertRaises(RuntimeError):
            initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM catalog_tables").fetchone()[0], 48)


class DocumentationImportTests(unittest.TestCase):
    def test_portable_paths_encoding_and_original_bytes(self):
        from import_documentations import DEFAULT_SOURCE, ROOT, import_documents
        self.assertEqual(DEFAULT_SOURCE, ROOT / 'documentation-source')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'Docs', root / 'hub'
            (source / 'schema').mkdir(parents=True)
            output.mkdir()
            original = source / 'schema' / 'guia ç # %.md'
            data = b'# Portable\r\n\r\n[missing](missing.md)\r\n'
            original.write_bytes(data)
            report = import_documents(source, output)
            self.assertTrue(report['written'])
            document = json.loads((output / 'documentations.json').read_text())['documents'][0]
            self.assertEqual(document['sourcePath'], 'schema/guia ç # %.md')
            self.assertEqual(document['sourceUrl'], '/documentation-files/schema/guia%20%C3%A7%20%23%20%25.md')
            self.assertEqual(document['content'], data.decode())
            self.assertEqual(original.read_bytes(), data)
            self.assertEqual((output / 'documentation-files' / document['sourcePath']).read_bytes(), data)
            self.assertTrue(import_documents(source, output)['written'])
            (output / 'documentation-files' / document['sourcePath']).write_bytes(b'different')
            with self.assertRaisesRegex(ValueError, 'existing_source_copy_differs'):
                import_documents(source, output)
            self.assertEqual(original.read_bytes(), data)


class ImportTests(DatabaseTests):
    def setUp(self):
        super().setUp()
        self.xlsx = Path(self.directory.name) / 'dictionary.xlsx'
        self.make_xlsx()

    def make_xlsx(self, count='2', formula=False, duplicate=False, merged=False, placeholder=False):
        sheets = {
            'Índice': [(1, {'A': 'Dicionário'})],
            'Operacional': [(2, {'B': 'Tabela'}),
                            (3, {'A': 'OP01 Teste', 'B': 'sample', 'C': count, 'D': 'Parcial', 'E': 'fonte.md'})],
            'Analítico': [(2, {'B': 'Tabela'}),
                          (3, {'A': 'AN01 Teste', 'B': 'unknown', 'C': '0', 'D': 'Colunas físicas ausentes', 'E': 'analytics.md'})],
            'OP01 Teste': [(2, {'F': 'ID do Contrato', 'G': 'Nome do Evento', 'J': 'Nome Propriedade'}),
                (3, {'F': 'mottainai.sample', 'G': 'sample', 'H': 'Descrição real', 'J': 'identifier',
                     'K': 'Identificador', 'L': 'BIGINT', 'M': 'sim', 'O': 'PK', 'Q': 'fonte.md:3'}),
                (4, {'F': 'mottainai.sample', 'G': 'sample', 'H': 'Descrição real',
                     'J': 'identifier' if duplicate else '*_masked', 'K': 'Família literal; sem expansão.'}),
                (5, {'G': 'Nota livre conservada integralmente'})],
            'AN01 Teste': [(2, {'F': 'ID do Contrato', 'G': 'Nome do Evento', 'J': 'Nome Propriedade'}),
                (3, {'F': 'mottainai_analytics.unknown', 'G': 'unknown', 'H': 'Objeto sem DDL', 'Q': 'Nenhuma coluna inventada.'})],
        }
        if merged:
            for column in ('G', 'H'):
                sheets['OP01 Teste'][2][1].pop(column)
        if placeholder:
            sheets['AN01 Teste'][1][1].update({'J': '—', 'K': 'Sem campos físicos', 'L': 'N/D'})
        namespace = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        tag = lambda name: '{' + namespace + '}' + name
        workbook = ET.Element(tag('workbook'))
        sheet_list = ET.SubElement(workbook, tag('sheets'))
        relations = ET.Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        with zipfile.ZipFile(self.xlsx, 'w') as archive:
            for index, (name, rows) in enumerate(sheets.items(), 1):
                ET.SubElement(sheet_list, tag('sheet'), name=name, sheetId=str(index),
                    attrib={'{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id': 'r' + str(index)})
                ET.SubElement(relations, 'Relationship', Id='r' + str(index), Target='worksheets/sheet' + str(index) + '.xml')
                root = ET.Element(tag('worksheet'))
                data = ET.SubElement(root, tag('sheetData'))
                for number, cells in rows:
                    row = ET.SubElement(data, tag('row'), r=str(number))
                    for column, value in cells.items():
                        cell = ET.SubElement(row, tag('c'), r=column + str(number), t='inlineStr')
                        ET.SubElement(ET.SubElement(cell, tag('is')), tag('t')).text = value
                        if formula and name == 'OP01 Teste' and number == 3 and column == 'J':
                            ET.SubElement(cell, tag('f')).text = '1+1'
                if merged and name == 'OP01 Teste':
                    merges = ET.SubElement(root, tag('mergeCells'))
                    for column in ('G', 'H'):
                        ET.SubElement(merges, tag('mergeCell'), ref=column + '3:' + column + '4')
                archive.writestr('xl/worksheets/sheet' + str(index) + '.xml', ET.tostring(root))
            archive.writestr('xl/workbook.xml', ET.tostring(workbook))
            archive.writestr('xl/_rels/workbook.xml.rels', ET.tostring(relations))

    def test_merged_metadata_and_placeholder_preserve_raw_source(self):
        self.make_xlsx(merged=True, placeholder=True)
        _, tables, structure = parse_catalog(self.xlsx)
        self.assertEqual(structure['columnCount'], 2)
        self.assertEqual(len(tables['mottainai.sample']['columns']), 2)
        self.assertEqual(tables['mottainai_analytics.unknown']['columns'], [])
        self.assertIn('Descrição: Sem campos físicos', tables['mottainai_analytics.unknown']['description'])
        self.assertNotIn('G', dict(read_xlsx(self.xlsx)['OP01 Teste'])[4])
        import_catalog(self.database, self.xlsx)
        with closing(read_connection(self.database)) as connection:
            raw = json.loads(connection.execute("SELECT cells_json FROM xlsx_rows WHERE sheet='OP01 Teste' AND row_number=4").fetchone()[0])
            self.assertNotIn('G', raw)
            self.assertNotIn('H', raw)

    def test_unmerged_missing_name_and_invalid_placeholder_are_rejected(self):
        for merged in (False, True):
            self.make_xlsx(merged=merged)
            with zipfile.ZipFile(self.xlsx) as archive:
                entries = {name: archive.read(name) for name in archive.namelist()}
            root = ET.fromstring(entries['xl/worksheets/sheet4.xml'])
            namespace = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            reference = 'J4' if merged else 'G4'
            cell = root.find(".//s:c[@r='" + reference + "']", namespace)
            cell.find('s:is/s:t', namespace).text = '—' if merged else ''
            entries['xl/worksheets/sheet4.xml'] = ET.tostring(root)
            with zipfile.ZipFile(self.xlsx, 'w') as archive:
                for name, data in entries.items():
                    archive.writestr(name, data)
            with self.assertRaises(ValueError):
                parse_catalog(self.xlsx)

    def test_import_preserves_demos_metadata_literals_and_unknown_columns(self):
        report = import_catalog(self.database, self.xlsx)
        self.assertEqual((report['insertedTables'], report['insertedColumns'], report['conflicts']), (2, 2, []))
        with closing(read_connection(self.database)) as connection:
            overview = get_overview(connection)
            self.assertEqual((overview['tableCount'], overview['columnCount']), (50, 338))
            table = list_tables(connection, 'mottainai.sample')[0]
            columns = get_table(connection, table['id'])['columns']
            self.assertIn('Descrição real', table['description'])
            self.assertIn('Tipagem: BIGINT', columns[0]['description'])
            self.assertIn('Obrigatório: sim', columns[0]['description'])
            self.assertEqual(columns[1]['name'], '*_masked')
            unknown = list_tables(connection, 'mottainai_analytics.unknown')[0]
            self.assertEqual(get_table(connection, unknown['id'])['columns'], [])
            self.assertIn('Nenhuma coluna inventada.', unknown['description'])
            self.assertEqual(connection.execute('SELECT count(*) FROM xlsx_rows').fetchone()[0], 11)
            raw = connection.execute("SELECT cells_json FROM xlsx_rows WHERE sheet='OP01 Teste' AND row_number=5").fetchone()[0]
            self.assertIn('Nota livre conservada integralmente', raw)
            self.assertEqual(connection.execute("SELECT count(*) FROM catalog_tables WHERE schema_name LIKE 'demo_%'").fetchone()[0], 48)
            self.assertIn('dictionary.xlsx', overview['source'])
        with closing(read_connection(Path(report['backup']))) as connection:
            self.assertEqual(len(list_tables(connection, '')), 48)
        # POSIX exposes the restrictive mode bits; Windows chmod semantics differ.
        if os.name != 'nt':
            self.assertEqual(Path(report['backup']).stat().st_mode & 0o777, 0o600)

    def test_reimport_is_idempotent_and_local_edits_are_not_overwritten(self):
        import_catalog(self.database, self.xlsx)
        second = import_catalog(self.database, self.xlsx)
        self.assertEqual((second['insertedTables'], second['insertedColumns'], second['conflicts']), (0, 0, []))
        with closing(sqlite3.connect(self.database)) as connection, connection:
            table_id = connection.execute("SELECT id FROM catalog_tables WHERE name='sample'").fetchone()[0]
            connection.execute("UPDATE catalog_tables SET description='local edit' WHERE id=?", (table_id,))
            connection.execute("UPDATE table_columns SET description='' WHERE table_id=? AND name='identifier'", (table_id,))
        third = import_catalog(self.database, self.xlsx)
        self.assertEqual((third['insertedTables'], third['insertedColumns'], len(third['conflicts'])), (0, 0, 2))
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(get_table(connection, table_id)['description'], 'local edit')
            self.assertEqual(get_table(connection, table_id)['columns'][0]['description'], '')
            self.assertEqual(connection.execute('SELECT count(*) FROM xlsx_sources').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT count(*) FROM xlsx_rows').fetchone()[0], 11)

    def test_existing_case_insensitive_identity_and_positions_are_preserved(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO catalog_tables VALUES ('local', 'MOTTAINAI', 'SAMPLE', '')")
            connection.execute("INSERT INTO table_columns(table_id,name,description,position) VALUES ('local','IDENTIFIER','local',5)")
            connection.execute("INSERT INTO table_columns(table_id,name,description,position) VALUES ('local','extra','extra local',9)")
        report = import_catalog(self.database, self.xlsx)
        self.assertEqual((report['insertedTables'], report['insertedColumns'], len(report['conflicts'])), (1, 1, 2))
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT name,position FROM table_columns WHERE table_id='local' ORDER BY position").fetchall()[2]['position'], 10)
            self.assertEqual(get_table(connection, 'local')['description'], '')
            self.assertEqual(get_table(connection, 'local')['columns'][0]['description'], 'local')

    def test_invalid_input_fails_before_backup_or_database_changes(self):
        for args in ({'count': '99'}, {'formula': True}, {'duplicate': True}):
            with self.subTest(args=args):
                self.make_xlsx(**args)
                with self.assertRaises(ValueError):
                    import_catalog(self.database, self.xlsx)
                self.assertEqual(list(Path(self.directory.name).glob('*.pre-xlsx-*')), [])
                with closing(read_connection(self.database)) as connection:
                    self.assertEqual(len(list_tables(connection, '')), 48)

    def test_transaction_rolls_back_after_insert_failure(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("CREATE TRIGGER reject_import BEFORE INSERT ON table_columns WHEN NEW.name='*_masked' BEGIN SELECT RAISE(ABORT,'test failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            import_catalog(self.database, self.xlsx)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(len(list_tables(connection, '')), 48)
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='xlsx_sources'").fetchone())
        self.assertEqual(len(list(Path(self.directory.name).glob('*.pre-xlsx-*'))), 1)

    def test_xml_declarations_and_external_worksheet_targets_are_rejected(self):
        for entry, content in (
            ('xl/workbook.xml', b'<!DOCTYPE workbook [<!ENTITY data "unsafe">]><workbook/>'),
            ('xl/_rels/workbook.xml.rels', b'<Relationships><Relationship Id="r1" Target="https://invalid.example/sheet.xml"/></Relationships>'),
        ):
            with self.subTest(entry=entry):
                self.make_xlsx()
                with zipfile.ZipFile(self.xlsx) as archive:
                    entries = {name: archive.read(name) for name in archive.namelist()}
                entries[entry] = content
                with zipfile.ZipFile(self.xlsx, 'w') as archive:
                    for name, data in entries.items():
                        archive.writestr(name, data)
                with self.assertRaises(ValueError):
                    read_xlsx(self.xlsx)

    def test_case_ambiguous_local_table_is_skipped(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO catalog_tables VALUES ('one','mottainai','sample','one')")
            connection.execute("INSERT INTO catalog_tables VALUES ('two','MOTTAINAI','SAMPLE','two')")
        result = import_catalog(self.database, self.xlsx)
        self.assertEqual((result['insertedTables'], result['insertedColumns'], len(result['conflicts'])), (1,0,1))
        self.assertEqual(result['conflicts'][0]['field'], 'identity')
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(get_table(connection,'one')['columns'], [])
            self.assertEqual(get_table(connection,'two')['description'], 'two')

    def test_backup_failure_prevents_import(self):
        with patch('import_catalog.read_connection', side_effect=sqlite3.OperationalError('backup failed')):
            with self.assertRaises(sqlite3.OperationalError):
                import_catalog(self.database, self.xlsx)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(len(list_tables(connection, '')), 48)

    def test_real_workbook_matches_declared_counts_and_keeps_gaps(self):
        xlsx = Path(__file__).resolve().parent / 'Tracking - Mottainai - Operacional e Analitico - Centralizado.xlsx'
        sheets, tables, structure = parse_catalog(xlsx)
        self.assertEqual((len(sheets), len(tables), structure['columnCount']), (28, 139, 883))
        self.assertEqual(len(structure['withoutColumns']), 39)
        self.assertEqual(len(structure['literalFieldNames']), 3)
        self.assertEqual(sum(len(table['columns']) for table in tables.values() if table['schema']=='mottainai'), 723)
        self.assertEqual(sum(len(table['columns']) for table in tables.values() if table['schema']=='mottainai_analytics'), 160)

    def test_real_workbook_import_adds_explicitly_inferred_fields(self):
        xlsx = Path(__file__).resolve().parent / 'Tracking - Mottainai - Operacional e Analitico - Centralizado.xlsx'
        report = import_catalog(self.database, xlsx)
        self.assertEqual(report['inferredColumnCount'], 16)
        with closing(read_connection(self.database)) as connection:
            for table_name, expected_fields in {
                'inventory_count': 8,
                'legacy_sync_record': 8,
            }.items():
                table = connection.execute('SELECT id FROM catalog_tables WHERE schema_name="mottainai" AND name=?', (table_name,)).fetchone()
                self.assertIsNotNone(table)
                fields = connection.execute('SELECT name, description FROM table_columns WHERE table_id=?', (table['id'],)).fetchall()
                self.assertEqual(len(fields), expected_fields)
                self.assertTrue(all('INFERIDO' in field['description'] and 'não confirmado por DDL' in field['description'] for field in fields))


class OverviewTests(DatabaseTests):
    def test_metrics_include_local_changes_and_ignore_blank_descriptions(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("UPDATE table_columns SET description=' \t\n\r ' WHERE id=(SELECT min(id) FROM table_columns)")
            connection.execute("INSERT INTO catalog_tables VALUES ('empty','empty_schema','empty_table','')")
        with closing(read_connection(self.database)) as connection:
            overview = get_overview(connection)
            self.assertEqual((overview['tableCount'], overview['columnCount'], overview['documentedColumnCount']), (49, 336, 335))
            self.assertEqual(overview['source'], 'SQLite local')
            self.assertEqual(overview['schemas'][-1], {'name':'empty_schema','tableCount':1})

    def test_empty_catalog_returns_zero_metrics(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DELETE FROM table_columns')
            connection.execute('DELETE FROM catalog_tables')
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(get_overview(connection), {'tableCount':0, 'columnCount':0,
                'documentedColumnCount':0, 'schemas':[], 'source':'SQLite local'})


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.database = Path(cls.directory.name) / "api.sqlite3"
        initialize_database(cls.database)
        cls.server = create_server(cls.database, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def setUp(self):
        self.cookie = ''
        self.csrf = ''
        self.server.login_failures.clear()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DELETE FROM documentation_catalog')
        self.login_as('USER')

    def login_as(self, role):
        self.cookie = ''
        credentials = {
            'DBA': ('databaseadmin@mottainai.com', 'senha@DBA1'),
            'FULLSTACK': ('fullstack@mottainai.com', 'senha@FullStack2'),
            'USER': ('comumuser@mottainai.com', 'senha@userComum3'),
        }
        email, password = credentials[role]
        status, headers, body = self.request('/api/login', 'POST', body={'email':email,'password':password})
        self.assertEqual(status, 200)
        self.cookie = headers['Set-Cookie'].split(';')[0]
        self.csrf = json.loads(body)['csrfToken']
        return json.loads(body)

    def request(self, path, method="GET", headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            request_headers = {'Cookie': self.cookie} if self.cookie else {}
            if method in ('POST', 'DELETE'):
                request_headers.update({'Origin': f'http://127.0.0.1:{self.server.server_port}', 'Content-Type':'application/json', 'X-CSRF-Token': self.csrf})
            request_headers.update(headers or {})
            payload = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
            connection.request(method, path, body=payload, headers=request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_documentations_and_original_files(self):
        from urllib.parse import quote
        with tempfile.TemporaryDirectory() as directory, patch('server.ROOT', Path(directory)):
            root = Path(directory)
            sources = root / 'documentation-files' / 'dad'
            sources.mkdir(parents=True)
            (sources / 'guia teste.pdf').write_bytes(b'%PDF-1.4 test')
            catalog = {'schemas': ['dad'], 'documents': [{'id': 'dad/guia', 'schema': 'dad', 'title': 'Guia', 'content': 'Texto real'}]}
            (root / 'documentations.json').write_text(json.dumps(catalog), encoding='utf-8')
            url = '/documentation-files/dad/' + quote('guia teste.pdf')
            special = 'guia ç # %.md'
            (sources / special).write_bytes(b'encoded original')
            self.assertEqual(self.request('/documentation-files/dad/' + quote(special, safe=''))[0], 200)
            for role in ('USER', 'DBA', 'FULLSTACK'):
                self.login_as(role)
                status, _, body = self.request('/api/documentations')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body), catalog)
                status, headers, body = self.request(url)
                self.assertEqual((status, headers['Content-Type'], body), (200, 'application/pdf', b'%PDF-1.4 test'))
                self.assertEqual(self.request(url, 'HEAD')[2], b'')
            for extension in ('.docx', '.html', '.svg', '.js', '.png', '.ttf'):
                (sources / ('attachment' + extension)).write_bytes(b'test original')
                status, headers, body = self.request('/documentation-files/dad/attachment' + extension)
                self.assertEqual((status, body), (200, b'test original'))
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                if extension in ('.docx', '.html', '.svg', '.ttf'):
                    self.assertEqual(headers['Content-Disposition'], 'attachment')
                if extension in ('.html', '.svg', '.js'):
                    self.assertEqual(headers['Content-Type'], 'text/plain; charset=utf-8')
            (sources / 'bad.exe').write_bytes(b'not allowed')
            self.assertEqual(self.request('/documentation-files/dad/bad.exe')[0], 404)
            for path in ('/documentation-files/../documentations.json', '/documentation-files/%2e%2e/documentations.json', '/documentation-files/dad/missing.pdf', url + '?x=1'):
                self.assertEqual(self.request(path)[0], 404)
            try:
                (sources / 'escape.pdf').symlink_to(root / 'documentations.json')
            except OSError as error:
                if os.name == 'nt' and getattr(error, 'winerror', None) == 1314:
                    self.skipTest('Criar symlink no Windows requer Developer Mode ou privilégio elevado.')
                raise
            self.assertEqual(self.request('/documentation-files/dad/escape.pdf')[0], 404)
            self.assertEqual(self.request('/api/documentations?x=1')[0], 400)
            self.assertEqual(self.request(url, headers={'Origin': 'https://attacker.invalid'})[0], 403)
            self.cookie = ''
            self.assertEqual(self.request('/api/documentations')[0], 401)
            self.assertEqual(self.request(url)[0], 401)

    def test_documentation_catalog_changes_persist_and_require_dba(self):
        catalog = {
            'schemas': ['persist-test'],
            'documents': [{'id': 'persist-test-doc', 'schema': 'persist-test', 'title': 'Guia persistente', 'content': 'Conteúdo gravado no servidor.'}],
        }
        status, _, _ = self.request('/api/documentations', 'POST', body=catalog)
        self.assertEqual(status, 403)
        self.login_as('DBA')
        status, _, body = self.request('/api/documentations', 'POST', body=catalog)
        self.assertEqual(status, 200, body)
        self.login_as('USER')
        status, _, body = self.request('/api/documentations')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), catalog)

    def test_all_corpus_originals_get_head_and_hashes(self):
        from urllib.parse import quote, unquote
        root = Path(__file__).resolve().parent
        documents = json.loads((root / 'documentations.json').read_text(encoding='utf-8'))['documents']
        originals_dir = root / 'documentation-files'
        originals = {
            path.relative_to(originals_dir).as_posix()
            for path in originals_dir.rglob('*')
            if path.is_file() and not path.is_symlink()
        }
        indexed_sources = {document['sourcePath'] for document in documents}
        self.assertEqual(len(documents), len(indexed_sources))
        self.assertEqual(indexed_sources, originals)
        for document in documents:
            relative = Path(document['sourcePath'])
            self.assertFalse(relative.is_absolute())
            self.assertNotIn('..', relative.parts)
            expected_url = '/documentation-files/' + '/'.join(quote(part, safe='') for part in relative.parts)
            self.assertEqual(document['sourceUrl'], expected_url)
            self.assertEqual(unquote(expected_url.removeprefix('/documentation-files/')), relative.as_posix())
            original = (root / 'documentation-files' / relative).read_bytes()
            with self.subTest(source=relative.as_posix()):
                status, headers, body = self.request(expected_url)
                self.assertEqual(status, 200)
                self.assertEqual(hashlib.sha256(body).digest(), hashlib.sha256(original).digest())
                self.assertEqual(int(headers['Content-Length']), len(original))
                status, head_headers, body = self.request(expected_url, 'HEAD')
                self.assertEqual((status, body), (200, b''))
                for header in ('Content-Type', 'Content-Length', 'X-Content-Type-Options', 'Content-Disposition'):
                    self.assertEqual(head_headers.get(header), headers.get(header))

    def test_list_and_detail(self):
        status, headers, body = self.request("/api/tables?q=demo_home")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["tables"]), 8)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
        status, _, body = self.request("/api/tables/table-1-1")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["columns"]), 7)

    def test_overview_contract_auth_queries_origin_and_head(self):
        for role in ('USER', 'DBA', 'FULLSTACK'):
            self.login_as(role)
            status, headers, body = self.request('/api/overview')
            self.assertEqual(status, 200)
            data = json.loads(body)
            self.assertEqual(set(data), {'tableCount','columnCount','documentedColumnCount','schemas','source'})
            self.assertEqual((data['tableCount'],data['columnCount'],data['documentedColumnCount']), (48,336,336))
            self.assertEqual(sum(schema['tableCount'] for schema in data['schemas']), 48)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(self.request('/api/overview', 'HEAD')[2], b'')
        for path in ('/api/overview?q=x','/api/overview?unknown=','/api/overview?q=a&q=b','/api/overview?' + 'a=' * 300):
            self.assertEqual(self.request(path)[0], 400)
        self.assertEqual(self.request('/api/overview', headers={'Host':'attacker.invalid'})[0], 403)
        self.assertEqual(self.request('/api/overview', headers={'Origin':'https://attacker.invalid'})[0], 403)
        self.cookie = ''
        self.assertEqual(self.request('/api/overview')[0], 401)
        self.cookie = 'sid=invalid'
        self.assertEqual(self.request('/api/overview')[0], 401)
        self.login_as('USER')
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE sessions SET expires_at=0')
        self.assertEqual(self.request('/api/overview')[0], 401)

    def test_authenticated_overview_reads_imported_database(self):
        xlsx = Path(__file__).resolve().parent / 'Tracking - Mottainai - Operacional e Analitico - Centralizado.xlsx'
        with tempfile.TemporaryDirectory() as directory:
            imported = Path(directory) / 'imported.sqlite3'
            initialize_database(imported)
            with closing(sqlite3.connect(imported)) as connection, connection:
                connection.execute('PRAGMA foreign_keys = ON')
                connection.execute('DELETE FROM catalog_tables')
            import_catalog(imported, xlsx)
            with closing(read_connection(imported)) as connection:
                expected = get_overview(connection)
                catalog_snapshot = list_tables(connection, '')
                mottainai_snapshot = list_tables(connection, 'mottainai')
                demo_snapshot = list_tables(connection, 'demo_')
            _, baseline, structure = parse_catalog(xlsx)
            baseline_names = {table['schema'] + '.' + table['name'] for table in baseline.values()}
            self.assertTrue(baseline_names <= {table['fullName'] for table in catalog_snapshot})
            self.assertGreaterEqual(expected['columnCount'], structure['columnCount'])
            original_database = self.server.database
            try:
                self.server.database = imported
                self.login_as('USER')
                status, _, body = self.request('/api/overview')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body), expected)
                self.assertEqual(expected['tableCount'], len(catalog_snapshot))
                self.assertEqual(sum(schema['tableCount'] for schema in expected['schemas']), len(catalog_snapshot))
                status, _, body = self.request('/api/tables')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)['tables'], catalog_snapshot)
                status, _, body = self.request('/api/tables?q=demo_')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)['tables'], demo_snapshot)
                self.assertIn('XLSX:', expected['source'])
                status, _, body = self.request('/api/tables?q=mottainai')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)['tables'], mottainai_snapshot)
            finally:
                self.server.database = original_database

    def test_empty_unknown_and_invalid_queries(self):
        self.assertEqual(json.loads(self.request("/api/tables?q=not_found")[2])["tables"], [])
        self.assertEqual(self.request("/api/tables/missing")[0], 404)
        for path in ["/api/tables?q=" + "a" * 257, "/api/tables?q=a&q=b", "/api/tables?other=1", "/api/tables/table-1-1?extra=1", "/api/tables/a/b"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 400)

    def test_no_write_endpoints(self):
        for method in ["PUT", "PATCH", "DELETE", "OPTIONS"]:
            with self.subTest(method=method):
                self.assertEqual(self.request("/api/tables", method)[0], 405)
        self.assertEqual(len(json.loads(self.request("/api/tables")[2])["tables"]), 48)

    def test_static_allowlist_prevents_database_and_source_exposure(self):
        for path in ["/catalog.sqlite3", "/server.py", "/test_server.py", "/../server.py", "/%2e%2e/server.py", "/.env", "/api.sqlite3"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        for path in ["/", "/index.html", "/styles.css", "/app.js"]:
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
        self.assertEqual(self.request("/", "HEAD")[2], b"")

    def test_host_and_origin_are_restricted(self):
        self.assertEqual(self.request("/api/tables", headers={"Host": "attacker.invalid"})[0], 403)
        self.assertEqual(self.request("/api/tables", headers={"Origin": "https://attacker.invalid"})[0], 403)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_roles_login_and_password_hashes(self):
        for role in ('DBA','FULLSTACK','USER'):
            result = self.login_as(role)
            self.assertEqual(result['user']['role'], role)
            self.assertNotIn('password', json.dumps(result))
            self.assertEqual(self.request('/api/tables')[0], 200)
        with closing(sqlite3.connect(self.database)) as connection:
            hashes = connection.execute('SELECT password_hash FROM users').fetchall()
            self.assertEqual(len(hashes), 3)
            self.assertTrue(all(row[0].startswith('scrypt$') for row in hashes))

    def test_invalid_login_and_rate_limit(self):
        self.cookie = ''
        for _ in range(10):
            status, _, body = self.request('/api/login','POST',body={'email':'unknown@example.invalid','password':'incorrect'})
            self.assertEqual(status, 401)
            self.assertEqual(json.loads(body)['error'],'E-mail ou senha inválidos.')
        self.assertEqual(self.request('/api/login','POST',body={'email':'unknown@example.invalid','password':'incorrect'})[0], 429)
        self.assertEqual(self.request('/api/session')[2], b'{"user": null}')

    def test_logout_expiry_and_anonymous_are_blocked(self):
        old_cookie = self.cookie
        self.assertEqual(self.request('/api/logout','POST')[0], 200)
        self.assertEqual(self.request('/api/tables')[0], 401)
        self.assertEqual(json.loads(self.request('/api/session')[2]), {'user':None})
        self.login_as('USER')
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE sessions SET expires_at=0')
        self.assertEqual(self.request('/api/tables/table-1-1')[0],401)
        self.cookie = ''
        self.assertEqual(self.request('/api/tables','POST',body={'schema':'demo','name':'test'})[0],401)
        self.cookie = old_cookie
        self.assertEqual(self.request('/api/tables')[0],401)

    def test_csrf_and_user_cannot_create(self):
        data={'schema':'demo','name':'not_allowed'}
        self.assertEqual(self.request('/api/tables','POST',headers={'X-CSRF-Token':''},body=data)[0],403)
        self.assertEqual(self.request('/api/tables','POST',body=data)[0],403)
        self.assertEqual(self.request('/api/logout','POST',headers={'Origin':''})[0],403)
        self.assertEqual(self.request('/api/register','POST',body={})[0],404)

    def test_privileged_creation_validation_duplicate_and_persistence(self):
        self.login_as('FULLSTACK')
        self.assertEqual(self.request('/api/tables', 'POST', body={'schema':'auth_test','name':'blocked'})[0], 403)
        for role in ('DBA',):
            self.login_as(role)
            data={'schema':'auth_test','name':'table_'+role.lower(),'description':'Descrição de teste','columns':[{'name':'identifier','description':'Identificador'}]}
            status, _, body = self.request('/api/tables','POST',body=data)
            self.assertEqual(status,201)
            table=json.loads(body)
            self.assertEqual(table['columns'], data['columns'])
            self.assertEqual(self.request('/api/tables','POST',body=data)[0],409)
            initialize_database(self.database)
            self.assertEqual(self.request('/api/tables/'+table['id'])[0],200)
        self.assertEqual(self.request('/api/tables','POST',body={'schema':'bad.schema','name':'invalid'})[0],400)
        self.assertEqual(self.request('/api/tables','POST',body={'schema':'demo','name':'duplicate_columns','columns':[{'name':'same'},{'name':'SAME'}]})[0],400)
        self.assertEqual(self.request('/api/tables','POST',body={'schema':'demo','name':'table','role':'DBA'})[0],400)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("DELETE FROM catalog_tables WHERE schema_name='auth_test'")
            connection.execute("DELETE FROM table_columns WHERE table_id NOT IN (SELECT id FROM catalog_tables)")

    def test_database_error_has_no_internal_details(self):
        for path in ('/api/tables', '/api/overview'):
            with self.subTest(path=path), patch("server.read_connection", side_effect=sqlite3.OperationalError("private database path")), self.assertLogs(level="ERROR"):
                status, _, body = self.request(path)
            self.assertEqual(status, 500)
            self.assertNotIn(b"private database path", body)


class ColumnAPITests(unittest.TestCase):
    request = APITests.request
    login_as = APITests.login_as

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / 'columns.sqlite3'
        initialize_database(self.database)
        self.server = create_server(self.database, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cookie = self.csrf = ''
        self.login_as('DBA')
        self.path = '/api/tables/table-1-1/columns'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def detail(self, table_id='table-1-1'):
        status, _, body = self.request('/api/tables/' + table_id)
        self.assertEqual(status, 200)
        return json.loads(body)

    def test_add_delete_order_snapshot_and_restart_preserve_catalog_and_users(self):
        with closing(read_connection(self.database)) as connection:
            tables = list_tables(connection, '')
            users = [tuple(row) for row in connection.execute('SELECT * FROM users ORDER BY id')]
            other_columns = [tuple(row) for row in connection.execute("SELECT * FROM table_columns WHERE table_id != 'table-1-1' ORDER BY id")]
        original = self.detail()
        added = {'name':'z_new', 'description':'Descrição ç ' + 'x' * 3988}
        status, _, body = self.request(self.path, 'POST', body=added)
        self.assertEqual(status, 201)
        expected = {**original, 'columns': original['columns'] + [added]}
        self.assertEqual(json.loads(body), expected)
        self.assertEqual(self.detail(), expected)
        status, _, body = self.request(self.path, 'DELETE', body={'name':'category'})
        self.assertEqual(status, 200)
        expected['columns'] = [column for column in expected['columns'] if column['name'] != 'category']
        self.assertEqual(json.loads(body), expected)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'a_new'})[0], 201)
        expected['columns'].append({'name':'a_new', 'description':''})
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        initialize_database(self.database)
        self.server = create_server(self.database, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assertEqual(self.detail(), expected)
        self.assertEqual(json.loads(self.request('/api/session')[2])['user']['role'], 'DBA')
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(list_tables(connection, ''), tables)
            self.assertEqual([tuple(row) for row in connection.execute('SELECT * FROM users ORDER BY id')], users)
            self.assertEqual([tuple(row) for row in connection.execute("SELECT * FROM table_columns WHERE table_id != 'table-1-1' ORDER BY id")], other_columns)
            positions = connection.execute("SELECT name,position FROM table_columns WHERE table_id='table-1-1' ORDER BY position").fetchall()
            self.assertEqual(tuple(positions[-1]), ('a_new', 8))

    def test_roles_auth_origin_csrf_and_unsupported_methods(self):
        original = self.detail()
        for role in ('USER', 'FULLSTACK'):
            self.login_as(role)
            for method in ('POST', 'DELETE'):
                self.assertEqual(self.request(self.path, method, body={'name':'record_id'})[0], 403)
        self.login_as('DBA')
        for method in ('POST', 'DELETE'):
            for headers in ({'Origin':''}, {'Origin':'https://attacker.invalid'}, {'Host':'attacker.invalid'}, {'X-CSRF-Token':''}, {'X-CSRF-Token':'wrong'}):
                with self.subTest(method=method, headers=headers):
                    self.assertEqual(self.request(self.path, method, headers=headers, body={'name':'record_id'})[0], 403)
            saved_cookie = self.cookie
            for cookie in ('', 'sid=invalid'):
                self.cookie = cookie
                self.assertEqual(self.request(self.path, method, body={'name':'record_id'})[0], 401)
            self.cookie = saved_cookie
        self.assertEqual(self.detail(), original)
        for method in ('PUT', 'PATCH', 'OPTIONS'):
            self.assertEqual(self.request(self.path, method, body={'name':'record_id'})[0], 405)
        self.assertEqual(self.request('/api/tables', 'DELETE')[0], 405)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE sessions SET expires_at=0')
        for method in ('POST', 'DELETE'):
            self.assertEqual(self.request(self.path, method, body={'name':'record_id'})[0], 401)

    def test_column_errors_are_clear_and_preserve_data(self):
        original = self.detail()
        status, _, body = self.request(self.path, 'DELETE', body={'name': 'missing'})
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)['error'], 'Não foi possível excluir: a coluna não existe nesta tabela. Atualize a página.')
        status, _, body = self.request(self.path, 'POST', body={'name': '1bad'})
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)['error'], 'Nome de coluna inválido. Use letras, números e sublinhado, começando com letra ou sublinhado.')
        self.assertEqual(self.detail(), original)

    def test_validation_json_query_name_description_and_unknown_keys(self):
        original = self.detail()
        common = [b'{', b'\xff', b'[]', b'null', {}, {'name':None}, {'name':1}, {'name':''}, {'name':' '}, {'name':'new', 'unknown':1}]
        additions = [{'name':name} for name in ('1bad', 'a.b', '*_ciphertext', 'a b', 'é', 'x' * 129, "x'); DELETE FROM users;--")]
        additions += [{'name':'new', 'description':value} for value in (None, 1, [], 'x' * 4001)]
        for method in ('POST', 'DELETE'):
            for body in common + (additions if method == 'POST' else [{'name':'record_id','description':''}]):
                with self.subTest(method=method, body=body):
                    self.assertEqual(self.request(self.path, method, body=body)[0], 400)
            for path in (self.path + '?q=x', self.path + '?name=a&name=b', '/api/tables//columns', '/api/tables/a/b/columns', '/api/tables/' + 'a' * 129 + '/columns'):
                self.assertEqual(self.request(path, method, body={'name':'new'})[0], 400)
            self.assertEqual(self.request(self.path, method, body=b'{}', headers={'Content-Type':'text/plain'})[0], 400)
            self.assertEqual(self.request(self.path, method)[0], 400)
        self.assertEqual(self.detail(), original)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'_' + 'x' * 127, 'description':'x' * 4000})[0], 201)

    def test_duplicate_missing_and_literal_deletion_is_parameterized(self):
        original = self.detail()
        for method in ('POST', 'DELETE'):
            self.assertEqual(self.request('/api/tables/missing/columns', method, body={'name':'new'})[0], 404)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'RECORD_ID'})[0], 409)
        self.assertEqual(self.request(self.path, 'DELETE', body={'name':'missing'})[0], 404)
        self.assertEqual(self.request(self.path, 'DELETE', body={'name':"' OR 1=1 --"})[0], 404)
        self.assertEqual(self.detail(), original)
        literals = ['*_ciphertext', '*_masked', "literal'); DELETE FROM users;--", 'a.b', ' literal ']
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executemany('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)', [('table-1-1', name, 'fonte', position) for position, name in enumerate(literals, 7)])
        for name in literals:
            self.assertEqual(self.request(self.path, 'DELETE', body={'name':name})[0], 200)
            self.assertEqual(self.request(self.path, 'DELETE', body={'name':name})[0], 404)
        self.assertEqual(self.detail(), original)
        self.assertEqual(json.loads(self.request('/api/session')[2])['user']['role'], 'DBA')

    def test_empty_table_add_delete_and_readd(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO catalog_tables VALUES ('empty','source','empty','preservada')")
        path = '/api/tables/empty/columns'
        original = self.detail('empty')
        self.assertEqual(original['columns'], [])
        self.assertEqual(self.request(path, 'DELETE', body={'name':'new'})[0], 404)
        for _ in range(2):
            self.assertEqual(self.request(path, 'POST', body={'name':'new'})[0], 201)
            status, _, body = self.request(path, 'DELETE', body={'name':'new'})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), original)

    def test_concurrent_additions_duplicates_and_limit_are_serialized(self):
        def concurrent(names):
            barrier = threading.Barrier(len(names))
            def add(name):
                barrier.wait(timeout=5)
                return self.request(self.path, 'POST', body={'name':name})[0]
            with ThreadPoolExecutor(max_workers=len(names)) as executor:
                return list(executor.map(add, names))
        self.assertEqual(concurrent(['parallel_a', 'parallel_b']), [201, 201])
        self.assertEqual(sorted(concurrent(['duplicate', 'DUPLICATE'])), [201, 409])
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("DELETE FROM table_columns WHERE table_id='table-1-1'")
            connection.executemany('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)', [('table-1-1', 'source_' + str(i), '', i * 2) for i in range(199)])
        self.assertEqual(sorted(concurrent(['last_a', 'last_b'])), [201, 400])
        original = self.detail()
        self.assertEqual(len(original['columns']), 200)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'SOURCE_0'})[0], 409)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'over_limit'})[0], 400)
        self.assertEqual(self.detail(), original)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO table_columns(table_id,name,description,position) VALUES ('table-1-1','*_ciphertext','fonte',500)")
        self.assertEqual(len(self.detail()['columns']), 201)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'over_limit'})[0], 400)
        self.assertEqual(self.request(self.path, 'DELETE', body={'name':'*_ciphertext'})[0], 200)
        self.assertEqual(self.request(self.path, 'DELETE', body={'name':'source_0'})[0], 200)
        self.assertEqual(self.request(self.path, 'POST', body={'name':'new_last'})[0], 201)
        with closing(read_connection(self.database)) as connection:
            positions = connection.execute("SELECT position FROM table_columns WHERE table_id='table-1-1' ORDER BY position").fetchall()
            self.assertEqual(positions[-1][0], 398)
            self.assertEqual(len(set(row[0] for row in positions)), 200)

    def test_transaction_failure_rolls_back_and_hides_details(self):
        original = self.detail()
        with patch('server.write_connection', side_effect=sqlite3.OperationalError('private path')), self.assertLogs(level='ERROR'):
            status, _, body = self.request(self.path, 'POST', body={'name':'new'})
        self.assertEqual(status, 500)
        self.assertNotIn(b'private path', body)
        with patch('server.get_table', side_effect=sqlite3.OperationalError('snapshot failed')), self.assertLogs(level='ERROR'):
            self.assertEqual(self.request(self.path, 'POST', body={'name':'rolled_back'})[0], 500)
        with patch('server.get_table', side_effect=sqlite3.OperationalError('snapshot failed')), self.assertLogs(level='ERROR'):
            self.assertEqual(self.request(self.path, 'DELETE', body={'name':'record_id'})[0], 500)
        self.assertEqual(self.detail(), original)


class TableDeleteAPITests(unittest.TestCase):
    request = APITests.request
    login_as = APITests.login_as
    tearDown = ColumnAPITests.tearDown
    confirmation = {'confirmation': 'DELeT@R', 'confirmed': True}

    def setUp(self):
        ColumnAPITests.setUp(self)
        self.path = '/api/tables/table-1-1'
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executemany('INSERT INTO scripts VALUES (?,?,?,?)', [
                ('target-script', 'table-1-1', 'DROP TABLE users;', '2026-01-01T00:00:00Z'),
                ('other-script', 'table-1-2', 'SELECT 1;', '2026-01-01T00:00:00Z'),
            ])

    def snapshot(self):
        with closing(read_connection(self.database)) as connection:
            return {name: [tuple(row) for row in connection.execute('SELECT * FROM ' + name + ' ORDER BY 1')]
                    for name in ('catalog_tables', 'table_columns', 'scripts', 'users')}

    def test_delete_cascades_only_target_updates_indicators_and_persists(self):
        before = self.snapshot()
        overview = json.loads(self.request('/api/overview')[2])
        with closing(read_connection(self.database)) as connection:
            sessions = [tuple(row) for row in connection.execute('SELECT * FROM sessions ORDER BY 1')]
        status, headers, body = self.request(self.path, 'DELETE', body=self.confirmation)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {'ok': True})
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(self.request(self.path)[0], 404)
        self.assertEqual(self.request(self.path + '/scripts')[0], 404)
        self.assertNotIn('table-1-1', [table['id'] for table in json.loads(self.request('/api/tables')[2])['tables']])
        after = self.snapshot()
        self.assertEqual(after['catalog_tables'], [row for row in before['catalog_tables'] if row[0] != 'table-1-1'])
        self.assertEqual(after['table_columns'], [row for row in before['table_columns'] if row[1] != 'table-1-1'])
        self.assertEqual(after['scripts'], [row for row in before['scripts'] if row[1] != 'table-1-1'])
        self.assertEqual(after['users'], before['users'])
        with closing(read_connection(self.database)) as connection:
            self.assertEqual([tuple(row) for row in connection.execute('SELECT * FROM sessions ORDER BY 1')], sessions)
            self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(), [])
        expected = {**overview, 'tableCount': 47, 'columnCount': 329, 'documentedColumnCount': 329,
                    'schemas': [{**schema, 'tableCount': schema['tableCount'] - (schema['name'] == 'demo_account_statement')}
                                for schema in overview['schemas']]}
        self.assertEqual(json.loads(self.request('/api/overview')[2]), expected)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        initialize_database(self.database)
        self.server = create_server(self.database, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assertEqual(self.request(self.path)[0], 404)
        for path in (self.path, '/api/tables/missing', '/api/tables/%27%20OR%201=1%20--'):
            self.assertEqual(self.request(path, 'DELETE', body=self.confirmation)[0], 404)
        self.assertEqual(self.snapshot(), after)

    def test_exact_confirmation_invalid_json_and_extra_fields_preserve_data(self):
        before = self.snapshot()
        invalid = [None, b'{', b'\xff', b'[]', b'null', {},
                   {'confirmation': 'DELeT@R'}, {'confirmed': True},
                   {**self.confirmation, 'extra': None}]
        invalid += [{**self.confirmation, 'confirmation': value}
                    for value in ('DELETE', 'delet@r', 'DELET@R', ' DELeT@R', 'DELeT@R ', 'DELeT@R\n', '', None, True, 1, [], {})]
        invalid += [{**self.confirmation, 'confirmed': value}
                    for value in (False, None, 0, 1, 'true', 'false', [], {})]
        for body in invalid:
            with self.subTest(body=body):
                self.assertEqual(self.request(self.path, 'DELETE', body=body)[0], 400)
                self.assertEqual(self.snapshot(), before)
        for headers in ({'Content-Type': 'text/plain'}, {'Content-Length': '0'}):
            self.assertEqual(self.request(self.path, 'DELETE', headers=headers, body=self.confirmation)[0], 400)
        for path in (self.path + '?q=x', '/api/tables/', '/api/tables/a/b', '/api/tables/' + 'a' * 129):
            self.assertEqual(self.request(path, 'DELETE', body=self.confirmation)[0], 400)
        self.assertEqual(self.snapshot(), before)

    def test_roles_session_origin_and_csrf_preserve_data(self):
        before = self.snapshot()
        for role in ('USER', 'FULLSTACK'):
            self.login_as(role)
            self.assertEqual(self.request(self.path, 'DELETE', body=self.confirmation)[0], 403)
        self.login_as('DBA')
        for headers in ({'Origin': ''}, {'Origin': 'https://attacker.invalid'}, {'Host': 'attacker.invalid'},
                        {'X-CSRF-Token': ''}, {'X-CSRF-Token': 'wrong'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(self.path, 'DELETE', headers=headers, body=self.confirmation)[0], 403)
        saved_cookie = self.cookie
        for cookie in ('', 'sid=invalid'):
            self.cookie = cookie
            self.assertEqual(self.request(self.path, 'DELETE', body=self.confirmation)[0], 401)
        self.cookie = saved_cookie
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE sessions SET expires_at=0')
        self.assertEqual(self.request(self.path, 'DELETE', body=self.confirmation)[0], 401)
        self.assertEqual(self.snapshot(), before)

    def test_column_delete_preserved_script_delete_rejected(self):
        before = self.snapshot()
        self.assertEqual(self.request(self.path + '/scripts', 'DELETE', body=self.confirmation)[0], 405)
        self.assertEqual(self.request(self.path + '/scripts/target-script', 'DELETE', body=self.confirmation)[0], 400)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.request(self.path + '/columns', 'DELETE', body={'name': 'category'})[0], 200)
        after = self.snapshot()
        self.assertEqual(after['catalog_tables'], before['catalog_tables'])
        self.assertEqual(after['scripts'], before['scripts'])
        self.assertEqual(len(after['table_columns']), len(before['table_columns']) - 1)

    def test_cascade_failure_rolls_back_everything_and_hides_details(self):
        before = self.snapshot()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON scripts BEGIN SELECT RAISE(ABORT, 'private cascade failure'); END")
        status, _, body = self.request(self.path, 'DELETE', body=self.confirmation)
        self.assertEqual(status, 409)
        self.assertNotIn(b'private cascade failure', body)
        self.assertEqual(self.snapshot(), before)
        with patch('server.write_connection', side_effect=sqlite3.OperationalError('private path')), self.assertLogs(level='ERROR'):
            status, _, body = self.request(self.path, 'DELETE', body=self.confirmation)
        self.assertEqual(status, 500)
        self.assertNotIn(b'private path', body)
        self.assertEqual(self.snapshot(), before)

    def test_empty_last_table_removes_schema_without_executing_stored_sql(self):
        from server import write_connection
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("INSERT INTO catalog_tables VALUES ('empty','unique_schema','empty','')")
            connection.execute("INSERT INTO scripts VALUES ('empty-script','empty','DROP TABLE users;','2026-01-01T00:00:00Z')")
        queries = []
        def traced_connection(path):
            self.assertEqual(Path(path).resolve(), self.database.resolve())
            connection = write_connection(path)
            connection.set_trace_callback(queries.append)
            return connection
        before = json.loads(self.request('/api/overview')[2])
        with patch('server.write_connection', side_effect=traced_connection) as connect:
            self.assertEqual(self.request('/api/tables/empty', 'DELETE', body=self.confirmation)[0], 200)
            self.assertEqual(connect.call_count, 1)
        self.assertTrue(any(query.startswith('DELETE FROM catalog_tables WHERE id=') for query in queries))
        self.assertFalse(any(query.startswith(('DROP ', 'ALTER ', 'DELETE FROM users')) for query in queries))
        after = json.loads(self.request('/api/overview')[2])
        self.assertEqual(after['tableCount'], before['tableCount'] - 1)
        self.assertEqual(after['columnCount'], before['columnCount'])
        self.assertEqual(after['documentedColumnCount'], before['documentedColumnCount'])
        self.assertNotIn('unique_schema', [schema['name'] for schema in after['schemas']])

    def test_concurrent_repeated_delete_has_one_success(self):
        barrier = threading.Barrier(2)
        def delete(_):
            barrier.wait(timeout=5)
            return self.request(self.path, 'DELETE', body=self.confirmation)[0]
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sorted(executor.map(delete, range(2))), [200, 404])


class ScriptValidatorTests(unittest.TestCase):
    def test_accepts_multi_alter_quotes_comments_and_literals(self):
        examples = [
            'ALTER TABLE source.target ADD COLUMN x INT;',
            'alter/* note ; DROP TABLE */table `SOURCE`."TARGET" add x INT;\n-- SELECT\nALTER TABLE source.target DROP COLUMN y;',
            "ALTER TABLE source.target ADD x VARCHAR(20) COMMENT 'CREATE TABLE; DELETE FROM users; it''s safe';",
            'ALTER TABLE source.target ADD "select" INT, MODIFY `create` DECIMAL(10,2);',
            "ALTER TABLE source.target COMMENT = 'DROP TABLE; /* ! */'; # ignored\n",
            'ALTER TABLE source.target ALTER COLUMN x SET DEFAULT 1;',
            'ALTER TABLE "odd""schema".`odd``table` ADD x INT',
        ]
        for sql in examples:
            schema, table = ('odd"schema', 'odd`table') if 'odd' in sql else ('source', 'target')
            with self.subTest(sql=sql):
                self.assertEqual(validated_script({'sql': sql}, schema, table), sql)

    def test_rejects_other_commands_disguises_and_incomplete_lexemes(self):
        prefix = 'ALTER TABLE source.target '
        invalid = [
            '', ' ', '; -- comment', 'SELECT 1', 'CREATE TABLE source.target(x INT)',
            prefix + 'ADD x INT; DELETE FROM users', prefix + 'ADD x INT SELECT 1',
            prefix + 'DROP TABLE users', prefix + 'ADD x INT DROP/**/TABLE users',
            prefix + 'ADD x INT; ALTER TABLE other.target ADD y INT',
            'ALTER TABLE source.other ADD x INT', 'ALTER TABLE target ADD x INT',
            'ALTER TABLE source.target.extra ADD x INT', 'ALTER TABLE source.target',
            prefix + '/* comment only */', prefix + 'ADD', prefix + 'ADD COLUMN',
            prefix + 'DROP COLUMN', prefix + 'COMMENT =', prefix + 'ADD x INT,',
            prefix + 'ADD COLUMN ()', prefix + 'ALTER COLUMN x', prefix + 'ADD "" INT',
            prefix + "COMMENT 'unterminated", prefix + 'ADD `unterminated INT',
            prefix + 'ADD "unterminated INT', prefix + 'ADD x INT /* unterminated',
            prefix + 'ADD x INT /*!50000 ; DROP TABLE users */',
            prefix + 'ADD x INT /*M! DROP TABLE users */',
            prefix + 'COMMENT $$SELECT 1$$', prefix + 'COMMENT $tag$ALTER TABLE$tag$',
            prefix + 'ADD x INT; "ALTER" TABLE source.target ADD y INT',
            prefix + 'ADD x INT; ALTER TABLE source.target DROP TABLE users',
            prefix + 'ADD x INT /* nested /* comment */ SELECT 1 */',
            prefix + 'ADD x DECIMAL(10,2', prefix + 'ADD x INT)',
            prefix + "COMMENT 'bad\\", prefix + 'ADD x INT\x00',
        ]
        for sql in invalid:
            with self.subTest(sql=sql), self.assertRaises(ValueError):
                validated_script({'sql': sql}, 'source', 'target')

    def test_length_and_body_boundaries(self):
        prefix = 'ALTER TABLE source.target ADD x INT --'
        maximum = prefix + 'x' * (20000 - len(prefix))
        self.assertEqual(validated_script({'sql': maximum}, 'source', 'target'), maximum)
        for data in ({}, {'sql': None}, {'sql': 1}, {'sql': []}, {'sql': 'x'},
                     {'sql': maximum + 'x'}, {'sql': maximum, 'role': 'DBA'}, []):
            with self.subTest(data_type=type(data)), self.assertRaises(ValueError):
                validated_script(data, 'source', 'target')


class ScriptAPITests(unittest.TestCase):
    request = APITests.request
    login_as = APITests.login_as
    tearDown = ColumnAPITests.tearDown

    sql = 'ALTER TABLE demo_account_statement.cleaned_account_statement_associates ADD COLUMN documented_only INT;'

    def setUp(self):
        ColumnAPITests.setUp(self)
        self.path = '/api/tables/table-1-1/scripts'

    def snapshot(self):
        with closing(read_connection(self.database)) as connection:
            return {name: [tuple(row) for row in connection.execute('SELECT * FROM ' + name + ' ORDER BY 1')]
                    for name in ('catalog_tables', 'table_columns', 'users')}

    def test_contract_order_restart_and_no_sql_execution(self):
        original = self.snapshot()
        self.assertEqual(json.loads(self.request(self.path)[2]), {'scripts': []})
        sqls = [self.sql, self.sql.replace('ADD COLUMN documented_only INT', 'DROP COLUMN record_id')]
        for sql in sqls:
            status, _, body = self.request(self.path, 'POST', body={'sql': sql})
            self.assertEqual(status, 201)
            result = json.loads(body)
            self.assertEqual(set(result), {'scripts'})
            script = result['scripts'][0]
            self.assertEqual(set(script), {'id', 'sql', 'createdAt'})
            self.assertTrue(all(isinstance(value, str) for value in script.values()))
            self.assertEqual(script['sql'], sql)
            self.assertRegex(script['createdAt'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
        self.assertEqual([item['sql'] for item in result['scripts']], sqls[::-1])
        self.assertEqual(len({item['id'] for item in result['scripts']}), 2)
        self.assertEqual(json.loads(self.request('/api/tables/table-1-2/scripts')[2]), {'scripts': []})
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        initialize_database(self.database)
        self.server = create_server(self.database, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assertEqual(json.loads(self.request(self.path)[2]), result)
        self.assertEqual(self.snapshot(), original)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 4)

    def test_roles_session_origin_csrf_and_methods(self):
        for role in ('USER', 'FULLSTACK', 'DBA'):
            self.login_as(role)
            self.assertEqual(self.request(self.path)[0], 200)
            if role != 'DBA':
                self.assertEqual(self.request(self.path, 'POST', body={'sql': self.sql})[0], 403)
        for headers in ({'Origin': ''}, {'Origin': 'https://attacker.invalid'},
                        {'Host': 'attacker.invalid'}, {'X-CSRF-Token': ''}, {'X-CSRF-Token': 'wrong'}):
            self.assertEqual(self.request(self.path, 'POST', headers=headers, body={'sql': self.sql})[0], 403)
        for method in ('PUT', 'PATCH', 'DELETE', 'OPTIONS'):
            self.assertEqual(self.request(self.path, method, body={'sql': self.sql})[0], 405)
        saved_cookie = self.cookie
        for cookie in ('', 'sid=invalid'):
            self.cookie = cookie
            for method in ('GET', 'POST'):
                self.assertEqual(self.request(self.path, method, body={'sql': self.sql})[0], 401)
        self.cookie = saved_cookie
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('UPDATE sessions SET expires_at=0')
        for method in ('GET', 'POST'):
            self.assertEqual(self.request(self.path, method, body={'sql': self.sql})[0], 401)

    def test_invalid_body_routes_and_sql_leave_no_scripts(self):
        original = self.snapshot()
        invalid = [b'{', b'\xff', b'[]', b'null', {}, {'sql': None}, {'sql': 1}, {'sql': []},
                   {'sql': ''}, {'sql': 'x' * 20001}, {'sql': self.sql, 'name': 'extra'},
                   {'sql': 'SELECT 1'}, {'sql': self.sql + ' DROP TABLE users'},
                   {'sql': self.sql.replace('demo_account_statement', 'other')},
                   {'sql': self.sql.replace('associates', 'other')},
                   {'sql': self.sql + '/*! SELECT 1 */'}]
        for body in invalid:
            with self.subTest(body_type=type(body)):
                self.assertEqual(self.request(self.path, 'POST', body=body)[0], 400)
        status, _, body = self.request(self.path, 'POST', body={'sql': 'SELECT sensitive_input'})
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body), {'error': 'Script inválido. Revise o comando ALTER TABLE e a tabela informada.'})
        self.assertNotIn(b'sensitive_input', body)
        self.assertEqual(json.loads(self.request(self.path, 'POST', body={'sql': self.sql + ' /*! SELECT 1 */'})[2]),
                         {'error': 'Script inválido. Revise o comando ALTER TABLE e a tabela informada.'})
        self.assertEqual(json.loads(self.request(self.path, 'POST', body=b'{')[2]),
                         {'error': 'Dados inválidos. Verifique os campos e o formato JSON.'})
        self.assertEqual(self.request(self.path, 'POST')[0], 400)
        self.assertEqual(self.request(self.path, 'POST', headers={'Content-Type': 'text/plain'}, body=b'{}')[0], 400)
        for method in ('GET', 'POST'):
            for path in (self.path + '?q=x', self.path + '?a=1&a=2', '/api/tables//scripts',
                         '/api/tables/a/b/scripts', '/api/tables/' + 'a' * 129 + '/scripts'):
                self.assertEqual(self.request(path, method, body={'sql': self.sql})[0], 400)
            self.assertEqual(self.request('/api/tables/missing/scripts', method, body={'sql': self.sql})[0], 404)
        self.assertEqual(json.loads(self.request(self.path)[2]), {'scripts': []})
        self.assertEqual(self.snapshot(), original)

    def test_multi_alter_quoted_sql_is_stored_verbatim(self):
        sql = ('-- CREATE TABLE;\nALTER/* split */TABLE `DEMO_ACCOUNT_STATEMENT`."CLEANED_ACCOUNT_STATEMENT_ASSOCIATES" '
               "ADD x VARCHAR(20) COMMENT 'CREATE TABLE; it''s a comment';\n"
               'ALTER TABLE demo_account_statement.cleaned_account_statement_associates DROP COLUMN y;')
        self.assertEqual(self.request(self.path, 'POST', body={'sql': sql})[0], 201)
        self.assertEqual(json.loads(self.request(self.path)[2])['scripts'][0]['sql'], sql)

    def test_failure_rolls_back_and_hides_details(self):
        with patch('server.list_scripts', side_effect=sqlite3.OperationalError('private path')), self.assertLogs(level='ERROR'):
            status, _, body = self.request(self.path, 'POST', body={'sql': self.sql})
        self.assertEqual(status, 500)
        self.assertNotIn(b'private path', body)
        self.assertEqual(json.loads(self.request(self.path)[2]), {'scripts': []})


class ScriptMigrationTests(DatabaseTests):
    def test_v2_migration_preserves_all_existing_data_and_script_fk(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DROP TABLE scripts')
            connection.execute('CREATE TABLE xlsx_sources(name TEXT)')
            connection.execute("INSERT INTO xlsx_sources VALUES ('preserved.xlsx')")
            connection.execute("UPDATE catalog_tables SET description='local preserved' WHERE id='table-1-1'")
            names = ('catalog_tables', 'table_columns', 'users', 'sessions', 'xlsx_sources')
            before = {name: connection.execute('SELECT * FROM ' + name).fetchall() for name in names}
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 4)
            self.assertEqual({name: connection.execute('SELECT * FROM ' + name).fetchall() for name in names}, before)
            connection.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO scripts VALUES ('bad','missing','SQL','2026-01-01T00:00:00Z')")
            connection.execute("INSERT INTO scripts VALUES ('saved','table-1-1','documented','2026-01-01T00:00:00Z')")
        initialize_database(self.database)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT id FROM scripts').fetchall(), [('saved',)])

    def test_v1_migration_creates_scripts_without_reseeding(self):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DROP TABLE scripts')
            connection.execute('DROP TABLE sessions')
            connection.execute('DROP TABLE users')
            connection.execute('PRAGMA user_version=1')
        initialize_database(self.database)
        initialize_database(self.database)
        with closing(read_connection(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM scripts').fetchone()[0], 0)
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 4)
            self.assertEqual(connection.execute('SELECT count(*) FROM catalog_tables').fetchone()[0], 48)


class ColumnRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.database = Path(cls.directory.name) / "requests.sqlite3"
        initialize_database(cls.database)
        cls.server = create_server(cls.database, 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def setUp(self):
        self.cookie = ''
        self.csrf = ''
        self.server.login_failures.clear()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute('DELETE FROM notifications')
            connection.execute('DELETE FROM request_actions')
            connection.execute('DELETE FROM column_requests')
        self.login_as('FULLSTACK')

    def login_as(self, role):
        self.cookie = ''
        credentials = {
            'DBA': ('databaseadmin@mottainai.com', 'senha@DBA1'),
            'FULLSTACK': ('fullstack@mottainai.com', 'senha@FullStack2'),
            'USER': ('comumuser@mottainai.com', 'senha@userComum3'),
        }
        email, password = credentials[role]
        status, headers, body = self.request('/api/login', 'POST', body={'email':email,'password':password})
        self.assertEqual(status, 200, f'Login as {role} failed: {body}')
        self.cookie = headers['Set-Cookie'].split(';')[0]
        self.csrf = json.loads(body)['csrfToken']
        return json.loads(body)

    def request(self, path, method="GET", headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            request_headers = {'Cookie': self.cookie} if self.cookie else {}
            if method in ('POST', 'DELETE'):
                request_headers.update({'Origin': f'http://127.0.0.1:{self.server.server_port}', 'Content-Type':'application/json', 'X-CSRF-Token': self.csrf})
            request_headers.update(headers or {})
            payload = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
            connection.request(method, path, body=payload, headers=request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_user_role_cannot_access_requests(self):
        self.login_as('USER')
        status, _, body = self.request('/api/requests')
        self.assertEqual(status, 403)
        self.assertIn('Acesso restrito', json.loads(body)['error'])

    def test_user_role_cannot_access_notifications(self):
        self.login_as('USER')
        status, _, body = self.request('/api/notifications')
        self.assertEqual(status, 403)

    def test_fullstack_creates_request_and_dba_receives_notification(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-1',
            'reason': 'Precisamos rastrear a data de expiração do token.',
            'columns': [{'name': 'expires_at', 'description': 'Timestamp de expiração'}],
        })
        self.assertEqual(status, 201, body)
        request = json.loads(body)
        self.assertEqual(request['status'], 'OPEN')
        self.assertEqual(request['tableName'], 'demo_home.cleaned_home_component_item_showed')
        self.assertEqual(len(request['columns']), 1)
        self.assertEqual(request['columns'][0]['name'], 'expires_at')
        self.assertEqual(len(request['history']), 1)
        self.assertEqual(request['history'][0]['action'], 'OPEN')
        self.login_as('DBA')
        status, _, body = self.request('/api/requests')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(len(data['open']), 1)
        self.assertEqual(data['open'][0]['id'], request['id'])
        status, _, body = self.request('/api/notifications')
        self.assertEqual(status, 200)
        notifications = json.loads(body)
        self.assertGreaterEqual(notifications['unreadCount'], 1)

    def test_fullstack_cannot_create_tables(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/tables', 'POST', body={
            'schema': 'test_schema', 'name': 'test_table', 'description': '', 'columns': [{'name': 'id', 'description': ''}],
        })
        self.assertEqual(status, 403)
        self.assertIn('Somente DBA', json.loads(body)['error'])

    def test_fullstack_cannot_add_columns_directly(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/tables/table-2-2/columns', 'POST', body={
            'name': 'new_column', 'description': 'should fail',
        })
        self.assertEqual(status, 403)
        self.assertIn('Somente DBA', json.loads(body)['error'])

    def test_dba_approves_adds_columns_automatically(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-3',
            'reason': 'Adicionar rastreamento de status de refund.',
            'columns': [
                {'name': 'refund_status', 'description': 'Status atual do refund'},
                {'name': 'refund_amount', 'description': 'Valor do refund'},
            ],
        })
        self.assertEqual(status, 201, body)
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'APPROVE',
            'revision': request['revision'],
        })
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual(result['status'], 'APPROVED')
        with closing(read_connection(self.database)) as connection:
            table = get_table(connection, 'table-2-3')
            column_names = [column['name'] for column in table['columns']]
            self.assertIn('refund_status', column_names)
            self.assertIn('refund_amount', column_names)

    def test_dba_rejects_requires_justification(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-4',
            'reason': 'Coluna de auditoria.',
            'columns': [{'name': 'audit_log', 'description': 'Log de auditoria'}],
        })
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'REJECT',
            'revision': request['revision'],
            'comment': 'Esta coluna já existe em outra tabela. Use-a de lá.',
        })
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual(result['status'], 'REJECTED')

    def test_dba_rejects_without_justification_fails(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-5',
            'reason': 'Motivo qualquer.',
            'columns': [{'name': 'test_col', 'description': ''}],
        })
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'REJECT',
            'revision': request['revision'],
        })
        self.assertEqual(status, 400)

    def test_fullstack_cannot_respond_to_comments(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-6',
            'reason': 'Motivo teste.',
            'columns': [{'name': 'test_column', 'description': ''}],
        })
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'COMMENT',
            'revision': request['revision'],
            'comment': 'Revise o nome da coluna.',
        })
        self.assertEqual(status, 200)
        updated = json.loads(body)
        self.login_as('FULLSTACK')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'COMMENT',
            'revision': updated['revision'],
            'comment': 'Tentativa de resposta.',
        })
        self.assertEqual(status, 403)

    def test_any_fullstack_can_cancel_any_request(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-7',
            'reason': 'Motivo original.',
            'columns': [{'name': 'cancel_test', 'description': ''}],
        })
        self.assertEqual(status, 201)
        request = json.loads(body)
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'CANCEL',
            'revision': request['revision'],
            'comment': 'Coluna já existe, pedido desnecessário.',
        })
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual(result['status'], 'CANCELLED')

    def test_dba_can_edit_column_names_and_descriptions_only(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-2-8',
            'reason': 'Motivo para edição.',
            'columns': [{'name': 'original_name', 'description': 'original desc'}],
        })
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'EDIT',
            'revision': request['revision'],
            'columns': [{'name': 'revised_name', 'description': 'revised description'}],
        })
        self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertEqual(result['columns'][0]['name'], 'revised_name')
        self.assertEqual(result['columns'][0]['description'], 'revised description')

    def test_dba_cannot_add_or_remove_columns_when_editing(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-1',
            'reason': 'Motivo.',
            'columns': [{'name': 'col_one', 'description': ''}],
        })
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'EDIT',
            'revision': request['revision'],
            'columns': [
                {'name': 'col_one', 'description': ''},
                {'name': 'col_two', 'description': ''},
            ],
        })
        self.assertEqual(status, 400)
        self.assertIn('Edite somente', json.loads(body)['error'])

    def test_duplicate_open_request_is_rejected(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-2',
            'reason': 'Primeiro pedido.',
            'columns': [{'name': 'dup_test', 'description': ''}],
        })
        self.assertEqual(status, 201)
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-2',
            'reason': 'Segundo pedido.',
            'columns': [{'name': 'dup_test_2', 'description': ''}],
        })
        self.assertEqual(status, 409)
        self.assertIn('Já existe uma solicitação aberta', json.loads(body)['error'])

    def test_exactly_duplicate_request_is_rejected(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-3',
            'reason': 'Pedido original.',
            'columns': [{'name': 'exact_dup', 'description': 'desc'}],
        })
        self.assertEqual(status, 201)
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'REJECT',
            'revision': request['revision'],
            'comment': 'Recusado para teste.',
        })
        self.assertEqual(status, 200)
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-3',
            'reason': 'Pedido original.',
            'columns': [{'name': 'exact_dup', 'description': 'desc'}],
        })
        self.assertEqual(status, 201, body)

    def test_request_history_limits_to_five_actions(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-4',
            'reason': 'Motivo.',
            'columns': [{'name': 'hist_test', 'description': ''}],
        })
        self.assertEqual(status, 201, body)
        request = json.loads(body)
        self.login_as('DBA')
        for i in range(6):
            status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
                'action': 'COMMENT',
                'revision': json.loads(body)['revision'],
                'comment': f'Comentário {i+1}',
            })
            self.assertEqual(status, 200, body)
        result = json.loads(body)
        self.assertLessEqual(len(result['history']), 5)

    def test_closed_requests_appear_in_closed_list(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-5',
            'reason': 'Motivo.',
            'columns': [{'name': 'closed_test', 'description': ''}],
        })
        self.assertEqual(status, 201, body)
        request = json.loads(body)
        self.login_as('DBA')
        status, _, body = self.request(f"/api/requests/{request['id']}", 'POST', body={
            'action': 'APPROVE',
            'revision': request['revision'],
        })
        self.assertEqual(status, 200)
        status, _, body = self.request('/api/requests')
        data = json.loads(body)
        self.assertEqual(len(data['open']), 0)
        self.assertGreaterEqual(len(data['closed']), 1)
        self.assertEqual(data['closed'][0]['status'], 'APPROVED')

    def test_notifications_are_delivered_to_correct_role(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-6',
            'reason': 'Teste notificação.',
            'columns': [{'name': 'notif_test', 'description': ''}],
        })
        self.assertEqual(status, 201, body)
        self.login_as('DBA')
        status, _, body = self.request('/api/notifications')
        self.assertEqual(status, 200)
        dba_data = json.loads(body)
        self.assertGreaterEqual(dba_data['unreadCount'], 1)
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/notifications')
        self.assertEqual(status, 200)
        fs_data = json.loads(body)
        self.assertEqual(fs_data['unreadCount'], 0)

    def test_migration_v4_creates_request_tables(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        temp_db = Path(temp_dir.name) / "migration.sqlite3"
        initialize_database(temp_db)
        with closing(sqlite3.connect(temp_db)) as connection, connection:
            connection.execute('DROP TABLE column_requests')
            connection.execute('DROP TABLE request_actions')
            connection.execute('DROP TABLE notifications')
            connection.execute('PRAGMA user_version=2')
        initialize_database(temp_db)
        with closing(sqlite3.connect(temp_db)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 4)
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn('column_requests', tables)
            self.assertIn('request_actions', tables)
            self.assertIn('notifications', tables)

    def test_request_cannot_add_column_that_already_exists(self):
        self.login_as('FULLSTACK')
        status, _, body = self.request('/api/requests', 'POST', body={
            'tableId': 'table-3-7',
            'reason': 'Tentativa de adicionar coluna existente.',
            'columns': [{'name': 'record_id', 'description': 'Já existe'}],
        })
        self.assertEqual(status, 409)
        self.assertIn('já existe', json.loads(body)['error'])


class ProductionBootstrapTests(unittest.TestCase):
    def test_production_database_has_only_configured_accounts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / 'production.sqlite3'
            roles = {
                'arthur@mottainai.com': 'DBA',
                'ana@mottainai.com': 'DBA',
                'gustavo@mottainai.com': 'DBA',
                'miguel@mottainai.com': 'DBA',
                'rebecca@mottainai.com': 'FULLSTACK',
                'kevin@mottainai.com': 'FULLSTACK',
                'joao.vitor@mottainai.com': 'FULLSTACK',
                'pedro@mottainai.com': 'FULLSTACK',
                'joao@mottainai.com': 'USER',
                'isabella@mottainai.com': 'USER',
                'luana@mottainai.com': 'USER',
                'giovanna@mottainai.com': 'USER',
            }
            bcrypt_hash = '$2b$12$' + 'A' * 53
            env = {
                'APP_ENV': 'production',
                'BOOTSTRAP_USERS_JSON': json.dumps([
                    {'email': email, 'role': role, 'passwordHash': bcrypt_hash}
                    for email, role in roles.items()
                ]),
            }
            with patch.dict('os.environ', env, clear=True):
                initialize_database(database)
            with closing(sqlite3.connect(database)) as connection:
                users = dict(connection.execute('SELECT email, role FROM users'))
            self.assertEqual(users, roles)

    def test_bcrypt_password_hashes_are_verified(self):
        import bcrypt
        from server import password_matches

        encoded = bcrypt.hashpw(b'simple-test-password', bcrypt.gensalt()).decode()
        self.assertTrue(password_matches('simple-test-password', encoded))
        self.assertFalse(password_matches('wrong-password', encoded))


if __name__ == "__main__":
    unittest.main()
