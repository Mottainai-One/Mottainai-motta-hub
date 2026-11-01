import argparse
import hashlib
import io
import json
import posixpath
import re
import sqlite3
import uuid
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import closing
from pathlib import Path

from server import read_connection, write_connection

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
DETAIL_HEADER = {'F': 'ID do Contrato', 'G': 'Nome do Evento', 'J': 'Nome Propriedade'}
FIELD_LABELS = {'K': 'Descrição', 'L': 'Tipagem', 'M': 'Obrigatório', 'N': 'Exemplo de Valores',
                'O': 'Complemento', 'P': 'Plataforma', 'Q': 'OBS', 'R': 'Métrica', 'S': 'Data Lake Table'}


def read_xlsx(path, resolve_merged=False):
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) > 1000 or sum(info.file_size for info in archive.infolist()) > 50 * 1024 * 1024:
            raise ValueError('Planilha excede os limites de leitura.')

        def xml(name):
            data = archive.read(name)
            if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                raise ValueError('Declarações XML não permitidas.')
            return ET.fromstring(data)

        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(item.itertext()) for item in xml('xl/sharedStrings.xml').findall('s:si', NS)]
        relationships = {item.attrib['Id']: item.attrib['Target']
                         for item in xml('xl/_rels/workbook.xml.rels')}
        sheets = {}
        for sheet in xml('xl/workbook.xml').find('s:sheets', NS):
            target = relationships[sheet.attrib[REL_ID]]
            target = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/' + target)
            if not target.startswith('xl/worksheets/'):
                raise ValueError('Worksheet inválida.')
            worksheet = xml(target)
            rows = []
            for row in worksheet.findall('s:sheetData/s:row', NS):
                values = {}
                for cell in row.findall('s:c', NS):
                    if cell.find('s:f', NS) is not None:
                        raise ValueError('Fórmulas não são importadas; forneça valores literais.')
                    value = cell.find('s:v', NS)
                    value = value.text or '' if value is not None else ''
                    if cell.attrib.get('t') == 's':
                        value = strings[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        inline = cell.find('s:is', NS)
                        value = ''.join(inline.itertext()) if inline is not None else ''
                    column = re.fullmatch(r'([A-Z]+)[1-9][0-9]*', cell.attrib['r'])
                    if not column:
                        raise ValueError('Referência de célula inválida.')
                    values[column[1]] = value
                if any(values.values()):
                    rows.append((int(row.attrib['r']), values))
            if resolve_merged:
                by_number = dict(rows)
                for merged in worksheet.findall('s:mergeCells/s:mergeCell', NS):
                    match = re.fullmatch(r'([GH])([1-9][0-9]*):\1([1-9][0-9]*)', merged.attrib.get('ref', ''))
                    if not match:
                        continue
                    column, start, end = match[1], int(match[2]), int(match[3])
                    if end < start or end > 1048576:
                        raise ValueError('Intervalo mesclado inválido.')
                    value = by_number.get(start, {}).get(column, '')
                    for number, values in rows:
                        if start <= number <= end and not values.get(column):
                            values[column] = value
            if sheet.attrib['name'] in sheets:
                raise ValueError('Abas repetidas.')
            sheets[sheet.attrib['name']] = rows
        return sheets


def parse_catalog(path):
    sheets = read_xlsx(path, resolve_merged=True)
    if not {'Índice', 'Operacional', 'Analítico'} <= sheets.keys():
        raise ValueError('Formato de dicionário Mottainai não reconhecido.')
    tables = {}
    summary = {}
    for sheet, schema in [('Operacional', 'mottainai'), ('Analítico', 'mottainai_analytics')]:
        rows = sheets[sheet]
        if not any(number == 2 and values.get('B') == 'Tabela' for number, values in rows):
            raise ValueError('Cabeçalho de resumo inválido.')
        for number, values in rows:
            if number <= 2:
                continue
            name = values.get('B', '').strip()
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', name):
                raise ValueError('Nome de tabela inválido no resumo.')
            key = schema + '.' + name
            if key in tables:
                raise ValueError('Tabela repetida no resumo.')
            try:
                count = int(values.get('C', ''))
            except ValueError as error:
                raise ValueError('Contagem de campos inválida.') from error
            if count < 0:
                raise ValueError('Contagem negativa.')
            summary[key] = count
            tables[key] = {'schema': schema, 'name': name, 'description': '', 'columns': [],
                           'context': values.get('A', ''), 'coverage': values.get('D', ''),
                           'document': values.get('E', ''), 'notes': []}
    field_rows = 0
    for sheet, rows in sheets.items():
        if sheet in ('Índice', 'Operacional', 'Analítico'):
            continue
        if not any(number == 2 and all(values.get(k) == v for k, v in DETAIL_HEADER.items()) for number, values in rows):
            raise ValueError('Cabeçalho de contexto inválido: ' + sheet)
        for number, values in rows:
            if number <= 2:
                continue
            contract = values.get('F', '').strip()
            if not contract:
                continue  # Notas livres ficam preservadas integralmente em xlsx_rows.
            if contract not in tables or values.get('G', '').strip() != tables[contract]['name']:
                raise ValueError('Contrato ausente do resumo ou nome divergente: ' + contract)
            table = tables[contract]
            description = values.get('H', '').strip()
            if table['description'] and description != table['description']:
                raise ValueError('Descrições divergentes: ' + contract)
            table['description'] = description
            name = values.get('J', '').strip()
            if name == '—':
                if summary[contract] != 0:
                    raise ValueError('Marcador sem campos diverge do resumo: ' + contract)
                name = ''
            if name:
                if any(column['name'].casefold() == name.casefold() for column in table['columns']):
                    raise ValueError('Campo repetido: ' + contract + '.' + name)
                text = '\n'.join(label + ': ' + values[key] for key, label in FIELD_LABELS.items() if values.get(key))
                table['columns'].append({'name': name, 'description': text})
                field_rows += 1
            else:
                if values.get('J', '').strip() == '—':
                    table['notes'].extend(label + ': ' + values[key] for key, label in
                                          FIELD_LABELS.items() if values.get(key) and key not in ('Q', 'S'))
                table['notes'].extend(label + ': ' + values[key] for key, label in
                                      {'I': 'Momento do disparo', 'Q': 'OBS', 'S': 'Data Lake Table'}.items() if values.get(key))
    for key, table in tables.items():
        if len(table['columns']) != summary[key]:
            raise ValueError('Contagem de campos diverge do resumo: ' + key)
        table['description'] = '\n'.join(filter(None, [table['description'],
            'Contexto: ' + table['context'], 'Cobertura: ' + table['coverage'],
            'Documento fonte: ' + table['document'], *dict.fromkeys(table['notes'])]))
    return sheets, tables, {'sheetCount': len(sheets), 'tableCount': len(tables), 'columnCount': field_rows,
        'schemas': dict(Counter(table['schema'] for table in tables.values())),
        'withoutColumns': [key for key, table in tables.items() if not table['columns']],
        'literalFieldNames': [key + '.' + column['name'] for key, table in tables.items() for column in table['columns']
                              if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', column['name'])]}


def import_catalog(database, xlsx):
    database, xlsx = Path(database).resolve(), Path(xlsx).resolve()
    # Ler e validar tudo antes do backup e de qualquer escrita no catálogo.
    data = xlsx.read_bytes()
    sheets, tables, structure = parse_catalog(io.BytesIO(data))
    sheets = read_xlsx(io.BytesIO(data))
    digest = hashlib.sha256(data).hexdigest()
    backup = database.with_name(database.stem + '.pre-xlsx-' + uuid.uuid4().hex + '.sqlite3')
    with backup.open('xb'):
        pass
    backup.chmod(0o600)
    with closing(read_connection(database)) as source, closing(sqlite3.connect(backup)) as destination:
        source.backup(destination)
    report = {'backup': str(backup), 'sha256': digest, 'structure': structure,
              'insertedTables': 0, 'insertedColumns': 0, 'conflicts': []}
    with closing(write_connection(database)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        if connection.execute('PRAGMA user_version').fetchone()[0] != 2:
            raise ValueError('Versão de catálogo incompatível.')
        connection.execute('CREATE TABLE IF NOT EXISTS xlsx_sources (sha256 TEXT PRIMARY KEY, name TEXT NOT NULL)')
        connection.execute('''CREATE TABLE IF NOT EXISTS xlsx_rows (
            source_sha256 TEXT NOT NULL REFERENCES xlsx_sources(sha256),
            sheet TEXT NOT NULL, row_number INTEGER NOT NULL, cells_json TEXT NOT NULL,
            PRIMARY KEY(source_sha256, sheet, row_number))''')
        connection.execute('INSERT OR IGNORE INTO xlsx_sources VALUES (?,?)', (digest, xlsx.name))
        for sheet, rows in sheets.items():
            connection.executemany('INSERT OR IGNORE INTO xlsx_rows VALUES (?,?,?,?)',
                [(digest, sheet, number, json.dumps(values, ensure_ascii=False, sort_keys=True)) for number, values in rows])
        for key, table in tables.items():
            existing = connection.execute('SELECT * FROM catalog_tables WHERE lower(schema_name)=lower(?) AND lower(name)=lower(?)',
                                          (table['schema'], table['name'])).fetchall()
            if len(existing) > 1:
                report['conflicts'].append({'table': key, 'field': 'identity', 'reason': 'Identidade local ambígua.'})
                continue
            if existing:
                table_id = existing[0]['id']
                if existing[0]['description'] != table['description']:
                    report['conflicts'].append({'table': key, 'field': 'description', 'reason': 'Descrição local preservada.'})
            else:
                table_id = 'xlsx-' + hashlib.sha256(key.encode()).hexdigest()[:32]
                connection.execute('INSERT INTO catalog_tables VALUES (?,?,?,?)',
                                   (table_id, table['schema'], table['name'], table['description']))
                report['insertedTables'] += 1
            position = connection.execute('SELECT coalesce(max(position),-1)+1 FROM table_columns WHERE table_id=?', (table_id,)).fetchone()[0]
            for column in table['columns']:
                existing_column = connection.execute('SELECT * FROM table_columns WHERE table_id=? AND lower(name)=lower(?)',
                                                     (table_id, column['name'])).fetchall()
                if existing_column:
                    if len(existing_column) > 1 or existing_column[0]['description'] != column['description']:
                        report['conflicts'].append({'table': key, 'field': column['name'], 'reason': 'Coluna local preservada.'})
                    continue
                connection.execute('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)',
                                   (table_id, column['name'], column['description'], position))
                position += 1
                report['insertedColumns'] += 1
    return report


def main():
    parser = argparse.ArgumentParser(description='Importação aditiva do dicionário XLSX, com backup SQLite e conflitos preservados.')
    parser.add_argument('xlsx', type=Path)
    parser.add_argument('--database', type=Path, default=Path(__file__).resolve().parent / 'catalog.sqlite3')
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    result = parse_catalog(args.xlsx)[2] if args.inspect else import_catalog(args.database, args.xlsx)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
