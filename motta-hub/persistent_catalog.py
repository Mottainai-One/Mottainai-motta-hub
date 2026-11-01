"""Durable catalog persistence in the Mottainai PostgreSQL database."""

import json
import os
from urllib.parse import unquote, urlsplit


DOCUMENTATION_TABLE = 'public.hub_documentation_catalog'
TABLE_CATALOG_TABLE = 'public.hub_table_catalog'


def _json_value(value):
    return json.loads(value) if isinstance(value, str) else value


class PostgresCatalogStore:
    def __init__(self, database_url):
        parsed = urlsplit(database_url)
        database_name = unquote(parsed.path.lstrip('/'))
        if parsed.scheme not in ('postgres', 'postgresql') or database_name.casefold() != 'mottainai':
            raise RuntimeError('HUB_DATABASE_URL precisa apontar para o database mottainai.')
        self.database_url = database_url

    @classmethod
    def from_environment(cls, required=False):
        database_url = os.environ.get('HUB_DATABASE_URL', '').strip()
        if not database_url:
            if required:
                raise RuntimeError('Configure HUB_DATABASE_URL com a conexão privada do database mottainai.')
            return None
        return cls(database_url)

    def connect(self):
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError('Dependência psycopg ausente; instale requirements.txt.') from error
        return psycopg.connect(self.database_url, connect_timeout=10)

    def initialize(self):
        statements = (
            f'''CREATE TABLE IF NOT EXISTS {DOCUMENTATION_TABLE} (
                id smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                schemas_json jsonb NOT NULL CHECK (jsonb_typeof(schemas_json) = 'array'),
                documents_json jsonb NOT NULL CHECK (jsonb_typeof(documents_json) = 'array'),
                updated_by_email text NOT NULL,
                updated_at timestamptz NOT NULL DEFAULT now()
            )''',
            f'''CREATE TABLE IF NOT EXISTS {TABLE_CATALOG_TABLE} (
                table_id text PRIMARY KEY,
                schema_name text NOT NULL,
                table_name text NOT NULL,
                description text NOT NULL DEFAULT '',
                columns_json jsonb NOT NULL CHECK (jsonb_typeof(columns_json) = 'array'),
                is_deleted boolean NOT NULL DEFAULT false,
                updated_by_email text NOT NULL,
                updated_at timestamptz NOT NULL DEFAULT now()
            )''',
        )
        with self.connect() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

    def load_documentations(self):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(f'SELECT schemas_json, documents_json FROM {DOCUMENTATION_TABLE} WHERE id=1')
            row = cursor.fetchone()
        if row is None:
            return None
        return {'schemas': _json_value(row[0]), 'documents': _json_value(row[1])}

    def save_documentations(self, schemas, documents, updated_by_email):
        from psycopg.types.json import Jsonb

        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(f'''INSERT INTO {DOCUMENTATION_TABLE}
                (id, schemas_json, documents_json, updated_by_email, updated_at)
                VALUES (1, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    schemas_json=EXCLUDED.schemas_json,
                    documents_json=EXCLUDED.documents_json,
                    updated_by_email=EXCLUDED.updated_by_email,
                    updated_at=now()''',
                (Jsonb(schemas), Jsonb(documents), updated_by_email))

    def save_table(self, table, updated_by_email, deleted=False):
        from psycopg.types.json import Jsonb

        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(f'''INSERT INTO {TABLE_CATALOG_TABLE}
                (table_id, schema_name, table_name, description, columns_json,
                 is_deleted, updated_by_email, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (table_id) DO UPDATE SET
                    schema_name=EXCLUDED.schema_name,
                    table_name=EXCLUDED.table_name,
                    description=EXCLUDED.description,
                    columns_json=EXCLUDED.columns_json,
                    is_deleted=EXCLUDED.is_deleted,
                    updated_by_email=EXCLUDED.updated_by_email,
                    updated_at=now()''',
                (table['id'], table['schema'], table['name'], table['description'],
                 Jsonb(table['columns']), deleted, updated_by_email))

    def load_table_changes(self):
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute(f'''SELECT table_id, schema_name, table_name, description,
                columns_json, is_deleted FROM {TABLE_CATALOG_TABLE} ORDER BY updated_at, table_id''')
            return [
                {'id': row[0], 'schema': row[1], 'name': row[2], 'description': row[3],
                 'columns': _json_value(row[4]), 'deleted': row[5]}
                for row in cursor.fetchall()
            ]

    def seed_table_catalog(self, tables):
        from psycopg.types.json import Jsonb

        with self.connect() as connection, connection.cursor() as cursor:
            cursor.executemany(f'''INSERT INTO {TABLE_CATALOG_TABLE}
                (table_id, schema_name, table_name, description, columns_json,
                 is_deleted, updated_by_email, updated_at)
                VALUES (%s, %s, %s, %s, %s, false, 'system:catalog-seed', now())
                ON CONFLICT (table_id) DO NOTHING''',
                [(table['id'], table['schema'], table['name'], table['description'], Jsonb(table['columns']))
                 for table in tables])
