"""Create the production catalog from the checked-in workbook during Render build."""

import os
import sqlite3
from pathlib import Path

import server


def main():
    os.environ['APP_ENV'] = 'production'
    database = Path(__file__).resolve().parent / 'catalog.sqlite3'
    if database.exists():
        raise RuntimeError('O build deve iniciar sem um catalog.sqlite3 pré-existente.')

    server.initialize_database(database)
    report = server.import_production_catalog(database)
    with sqlite3.connect(database) as connection:
        table_count = connection.execute('SELECT count(*) FROM catalog_tables').fetchone()[0]
        column_count = connection.execute('SELECT count(*) FROM table_columns').fetchone()[0]
        users_by_role = dict(connection.execute('SELECT role, count(*) FROM users GROUP BY role'))
        user_count = sum(users_by_role.values())

    if (table_count < 1 or column_count < 1 or user_count != 12
            or users_by_role != {'DBA': 4, 'FULLSTACK': 4, 'USER': 4}):
        raise RuntimeError('O catálogo ou as 12 contas de produção não foram inicializados corretamente.')
    print(f"Catálogo preparado: {table_count} tabelas, {column_count} colunas; "
          f"{report['insertedTables']} tabelas e {report['insertedColumns']} colunas importadas da planilha.")
    print('Contas de produção inicializadas: 4 DBA, 4 FULLSTACK e 4 USER.')


if __name__ == '__main__':
    main()
