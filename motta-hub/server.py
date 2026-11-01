import argparse
import json
import logging
import hashlib
import hmac
import os
import re
import secrets
import time
import threading
from http.cookies import SimpleCookie, CookieError
import sqlite3
import unicodedata
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent
PUBLIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFD", value)
                   if not unicodedata.combining(char)).lower().strip()


def initialize_database(path):
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version in (1, 2, 4):
                if version == 1:
                    migrate_auth(connection)
                migrate_scripts(connection)
                migrate_requests(connection)
                connection.commit()
                return
            if version != 0 or connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone():
                raise RuntimeError("Banco existente com versão de schema incompatível.")
            connection.execute("""
                CREATE TABLE catalog_tables (
                    id TEXT PRIMARY KEY NOT NULL,
                    schema_name TEXT NOT NULL CHECK(length(trim(schema_name)) > 0),
                    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                    description TEXT NOT NULL DEFAULT '',
                    UNIQUE(schema_name, name)
                )
            """)
            connection.execute("""
                CREATE TABLE table_columns (
                    id INTEGER PRIMARY KEY,
                    table_id TEXT NOT NULL REFERENCES catalog_tables(id) ON DELETE CASCADE,
                    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                    description TEXT NOT NULL DEFAULT '',
                    position INTEGER NOT NULL CHECK(position >= 0),
                    UNIQUE(table_id, name),
                    UNIQUE(table_id, position)
                )
            """)
            if os.environ.get('APP_ENV', '').lower() != 'production':
                seed_database(connection)
            migrate_auth(connection)
            migrate_scripts(connection)
            migrate_requests(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def seed_database(connection):
    groups = [
        ("demo_account_statement", ["associates", "associates_types", "movement_codes", "movements_cards", "movements_types", "refunds", "sources_of_funding", "statements"]),
        ("demo_home", ["component_item_showed", "component_item_viewed", "component_item_clicked", "screen_viewed", "button_clicked", "campaigns", "sessions", "navigation"]),
        ("demo_payments", ["transactions", "payment_methods", "settlements", "refunds", "recipients", "statuses", "daily_summary", "transaction_events"]),
        ("demo_orders", ["orders", "order_items", "products", "categories", "deliveries", "coupons", "inventory", "daily_sales"]),
        ("demo_customers", ["profiles", "preferences", "segments", "journeys", "contact_channels", "consents", "activity", "engagement"]),
        ("demo_analytics", ["daily_metrics", "monthly_metrics", "conversion_funnel", "cohorts", "retention", "usage_summary", "quality_audits", "table_catalog"]),
    ]
    for group_index, (schema, names) in enumerate(groups):
        entity = "event" if group_index == 1 else "order" if group_index == 3 else "record"
        columns = [
            (f"{entity}_id", "Identificador sintético e único do registro de demonstração."),
            ("reference_id", "Referência fictícia para associação com outros registros de teste."),
            ("category", "Categoria gerada para exercitar filtros e consultas."),
            ("status", "Situação do registro fictício: ativo, pendente ou concluído."),
            ("sample_value", "Valor numérico artificial, sem significado financeiro real."),
            ("created_at", "Data e hora simuladas da criação do registro."),
            ("updated_at", "Data e hora simuladas da última atualização do registro."),
        ]
        for index, name in enumerate(names):
            table_id = f"table-{group_index + 1}-{index + 1}"
            prefix = "analytics" if group_index == 5 else "cleaned"
            table_name = f"{prefix}_{schema.removeprefix('demo_')}_{name}"
            connection.execute(
                "INSERT INTO catalog_tables(id, schema_name, name, description) VALUES (?, ?, ?, ?)",
                (table_id, schema, table_name, f"Tabela de demonstração com registros fictícios de {name.replace('_', ' ')}."),
            )
            connection.executemany(
                "INSERT INTO table_columns(table_id, name, description, position) VALUES (?, ?, ?, ?)",
                [(table_id, column, description, position) for position, (column, description) in enumerate(columns)],
            )


def migrate_auth(connection):
    connection.execute("""CREATE TABLE users (
        id TEXT PRIMARY KEY NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('DBA', 'FULLSTACK', 'USER'))
    )""")
    connection.execute("""CREATE TABLE sessions (
        token_hash TEXT PRIMARY KEY NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        csrf_token TEXT NOT NULL,
        expires_at INTEGER NOT NULL
    )""")
    if os.environ.get('APP_ENV', '').lower() == 'production':
        try:
            bootstrap_users = json.loads(os.environ.get('BOOTSTRAP_USERS_JSON', ''))
        except json.JSONDecodeError as error:
            raise RuntimeError('BOOTSTRAP_USERS_JSON precisa conter uma lista JSON válida.') from error
        if not isinstance(bootstrap_users, list) or len(bootstrap_users) != 12:
            raise RuntimeError('BOOTSTRAP_USERS_JSON precisa conter as 12 contas configuradas para o Hub.')
        seen_emails = set()
        for user in bootstrap_users:
            if not isinstance(user, dict) or set(user) != {'email', 'role', 'passwordHash'}:
                raise RuntimeError('Cada conta precisa conter somente email, role e passwordHash.')
            email = user['email'].strip().lower() if isinstance(user['email'], str) else ''
            role = user['role']
            password_hash = user['passwordHash']
            email_key = email.casefold()
            if (not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email)
                    or email_key in seen_emails
                    or not isinstance(role, str)
                    or role not in {'DBA', 'FULLSTACK', 'USER'}
                    or not isinstance(password_hash, str)
                    or not re.fullmatch(r'\$2[aby]\$(?:0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}', password_hash)):
                raise RuntimeError('BOOTSTRAP_USERS_JSON contém e-mail, papel ou hash bcrypt inválido.')
            seen_emails.add(email_key)
            user_id = 'bootstrap-' + hashlib.sha256(email_key.encode()).hexdigest()[:24]
            connection.execute('INSERT INTO users VALUES (?,?,?,?)', (user_id, email, password_hash, role))
    else:
        connection.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", [
            ('demo-dba', 'databaseadmin@mottainai.com', 'scrypt$383029c7958494255121deb5762e4a49$d244240b5b5c6e3a59774d869687be630ef4d26199abd82651711723caa9834e0ca9f02c086e1cdfa289c69893e67ba1827f54e02e2adf8bd58fb55156121cb8', 'DBA'),
            ('demo-fullstack', 'fullstack@mottainai.com', 'scrypt$ef86a24970307a7c6488aef382abd4ff$43a5eb8fa94d9eafc19d4ca4cf588acce70aed816897f281ee8a52fba3bdb1da01d3fd3772e74291e4b7945efed932ed74119e998ca788c79ba5c3c6b38ed1e1', 'FULLSTACK'),
            ('demo-user', 'comumuser@mottainai.com', 'scrypt$c879146ba1c93d6eba96d11fde886c58$db3fa78c5967963f8cceb0151b324b3fc3a7778e979f4441ee3f78c9118d1835425307405eb6aa30d44b212e62826b1dd8b48a01f3eb580a2d679f7cb5b2d4e9', 'USER'),
        ])
    connection.execute('PRAGMA user_version = 2')


def migrate_scripts(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS scripts (
        id TEXT PRIMARY KEY NOT NULL,
        table_id TEXT NOT NULL REFERENCES catalog_tables(id) ON DELETE CASCADE,
        sql TEXT NOT NULL CHECK(length(sql) BETWEEN 1 AND 20000),
        created_at TEXT NOT NULL
    )""")


def migrate_requests(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS column_requests (
        id TEXT PRIMARY KEY NOT NULL,
        table_id TEXT NOT NULL REFERENCES catalog_tables(id) ON DELETE RESTRICT,
        table_name TEXT NOT NULL,
        reason TEXT NOT NULL CHECK(length(trim(reason)) BETWEEN 1 AND 4000),
        columns_json TEXT NOT NULL,
        fingerprint TEXT NOT NULL,
        author_id TEXT NOT NULL REFERENCES users(id),
        status TEXT NOT NULL CHECK(status IN ('OPEN', 'APPROVED', 'REJECTED', 'CANCELLED')),
        created_at TEXT NOT NULL,
        closed_at TEXT,
        revision INTEGER NOT NULL DEFAULT 0
    )""")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_open_request ON column_requests(table_id) WHERE status='OPEN'")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS duplicate_open_request ON column_requests(fingerprint) WHERE status='OPEN'")
    connection.execute("""CREATE TABLE IF NOT EXISTS request_actions (
        id INTEGER PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES column_requests(id),
        author_id TEXT NOT NULL REFERENCES users(id),
        author TEXT NOT NULL,
        action TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    connection.execute('CREATE INDEX IF NOT EXISTS actions_by_request ON request_actions(request_id, id DESC)')
    connection.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        request_id TEXT NOT NULL REFERENCES column_requests(id),
        action TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        read_at TEXT
    )""")
    connection.execute('CREATE INDEX IF NOT EXISTS notifications_by_user ON notifications(user_id, id DESC)')
    connection.execute("""CREATE TABLE IF NOT EXISTS documentation_catalog (
        id INTEGER PRIMARY KEY CHECK(id = 1),
        schemas_json TEXT NOT NULL,
        documents_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    connection.execute('PRAGMA user_version = 4')


class RequestError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def required_comment(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise RequestError(400, 'Informe um comentário ou justificativa de até 4000 caracteres.')
    return value.strip()


def request_columns(columns):
    try:
        _, _, _, columns = validated_table({'schema': '_', 'name': '_', 'columns': columns})
    except ValueError as error:
        raise RequestError(400, str(error)) from error
    if not columns:
        raise RequestError(400, 'Informe pelo menos uma coluna.')
    return [{'name': column['name'], 'description': column.get('description', '')} for column in columns]


def validated_documentation_catalog(data):
    if not isinstance(data, dict) or set(data) != {'schemas', 'documents'}:
        raise ValueError('Catálogo de documentações inválido.')
    schemas, documents = data['schemas'], data['documents']
    if not isinstance(schemas, list) or not isinstance(documents, list) or len(schemas) > 128 or len(documents) > 500:
        raise ValueError('Quantidade de seções ou documentos inválida.')
    normalized_schemas = set()
    for schema in schemas:
        if not isinstance(schema, str) or not schema.strip() or len(schema) > 128:
            raise ValueError('Nome de seção inválido.')
        key = schema.casefold()
        if key in normalized_schemas:
            raise ValueError('Seções repetidas.')
        normalized_schemas.add(key)
    clean_documents, seen_ids = [], set()
    allowed = {'id', 'schema', 'title', 'content', 'sourcePath', 'sourceUrl', 'filename', 'format'}
    for document in documents:
        if not isinstance(document, dict) or set(document) - allowed:
            raise ValueError('Documento inválido.')
        if not {'id', 'schema', 'title', 'content'} <= set(document):
            raise ValueError('Documento sem identificador, seção, título ou conteúdo.')
        identifier, schema, title, content = (document[key] for key in ('id', 'schema', 'title', 'content'))
        if (not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 512
                or identifier in seen_ids or not isinstance(schema, str) or schema.casefold() not in normalized_schemas
                or not isinstance(title, str) or not title.strip() or len(title) > 160
                or not isinstance(content, str) or len(content) > 200_000
                or not content.strip() and not document.get('sourceUrl')):
            raise ValueError('Identificador, seção, título ou conteúdo de documento inválido.')
        seen_ids.add(identifier)
        clean = {'id': identifier, 'schema': schema, 'title': title, 'content': content}
        source_path = document.get('sourcePath')
        if source_path is not None:
            if (not isinstance(source_path, str) or not source_path or source_path.startswith(('/', '\\'))
                    or '\\' in source_path or any(part in ('', '.', '..') for part in source_path.split('/'))):
                raise ValueError('Caminho de origem inválido.')
            clean['sourcePath'] = source_path
        source_url = document.get('sourceUrl')
        if source_url is not None:
            if not isinstance(source_url, str) or not source_url.startswith('/documentation-files/') or '?' in source_url or '#' in source_url:
                raise ValueError('URL de origem inválida.')
            clean['sourceUrl'] = source_url
        for key in ('filename', 'format'):
            value = document.get(key)
            if value is not None:
                limit = 255 if key == 'filename' else 32
                if not isinstance(value, str) or len(value) > limit:
                    raise ValueError('Metadado de origem inválido.')
                clean[key] = value
        clean_documents.append(clean)
    return schemas, clean_documents


def check_request_columns(connection, table_id, columns):
    existing = {row[0].lower() for row in connection.execute('SELECT name FROM table_columns WHERE table_id=?', (table_id,))}
    if any(column['name'].lower() in existing for column in columns):
        raise RequestError(409, 'Uma das colunas já existe no catálogo. O DBA deve revisar os nomes.')
    if len(existing) + len(columns) > 200:
        raise RequestError(400, 'A aprovação ultrapassaria o limite de 200 colunas da tabela.')


def get_request(connection, request_id):
    row = connection.execute('''SELECT r.*, u.email AS author FROM column_requests r
        JOIN users u ON u.id=r.author_id WHERE r.id=?''', (request_id,)).fetchone()
    if row is None:
        return None
    result = {key: row[key] for key in ('id', 'reason', 'author', 'status', 'revision')}
    result.update(tableId=row['table_id'], tableName=row['table_name'], createdAt=row['created_at'], closedAt=row['closed_at'], columns=json.loads(row['columns_json']))
    result['commented'] = bool(connection.execute("SELECT 1 FROM request_actions WHERE request_id=? AND action='COMMENT' LIMIT 1", (request_id,)).fetchone())
    result['history'] = [dict(action) for action in connection.execute('''SELECT id, author, action, content, created_at AS createdAt
        FROM request_actions WHERE request_id=? ORDER BY id DESC LIMIT 5''', (request_id,))]
    return result


def record_request_action(connection, request_id, session, action, content):
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    connection.execute('''INSERT INTO request_actions(request_id,author_id,author,action,content,created_at)
        VALUES (?,?,?,?,?,?)''', (request_id, session['id'], session['email'], action, content, stamp))
    recipient_role = 'DBA' if action in ('OPEN', 'CANCEL') else 'FULLSTACK' if action in ('COMMENT', 'APPROVE', 'REJECT') else None
    if recipient_role:
        table_name = connection.execute('SELECT table_name FROM column_requests WHERE id=?', (request_id,)).fetchone()[0]
        connection.execute('''INSERT INTO notifications(user_id,request_id,action,content,created_at)
            SELECT id,?,?,?,? FROM users WHERE role=?''', (request_id, action, table_name + ': ' + content, stamp, recipient_role))


def mutate_request(connection, session, request_id, data):
    if request_id is None:
        if session['role'] != 'FULLSTACK':
            raise RequestError(403, 'Somente FullStack pode solicitar colunas.')
        if set(data) != {'tableId', 'reason', 'columns'}:
            raise RequestError(400, 'Informe somente tabela, motivo e colunas. Não envie script.')
        table_id = data['tableId']
        if not isinstance(table_id, str) or not 1 <= len(table_id) <= 128:
            raise RequestError(400, 'Tabela inválida.')
        reason, columns = required_comment(data['reason']), request_columns(data['columns'])
        table = connection.execute('SELECT schema_name || \'.\' || name FROM catalog_tables WHERE id=?', (table_id,)).fetchone()
        if table is None:
            raise RequestError(404, 'Tabela não encontrada.')
        fingerprint = hashlib.sha256(json.dumps([table_id, reason, columns], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if connection.execute("SELECT 1 FROM column_requests WHERE fingerprint=? AND status='OPEN'", (fingerprint,)).fetchone():
            raise RequestError(409, 'Esta solicitação idêntica já está em processamento.')
        if connection.execute("SELECT 1 FROM column_requests WHERE table_id=? AND status='OPEN'", (table_id,)).fetchone():
            raise RequestError(409, 'Já existe uma solicitação aberta para esta tabela.')
        check_request_columns(connection, table_id, columns)
        request_id = secrets.token_hex(16)
        connection.execute('''INSERT INTO column_requests(id,table_id,table_name,reason,columns_json,fingerprint,author_id,status,created_at)
            VALUES (?,?,?,?,?,?,?,'OPEN',?)''', (request_id, table_id, table[0], reason, json.dumps(columns, ensure_ascii=False), fingerprint, session['id'], time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
        record_request_action(connection, request_id, session, 'OPEN', reason + '\n' + json.dumps(columns, ensure_ascii=False))
        return get_request(connection, request_id)
    action = data.get('action')
    allowed = {'CANCEL'} if session['role'] == 'FULLSTACK' else {'EDIT', 'COMMENT', 'APPROVE', 'REJECT'} if session['role'] == 'DBA' else set()
    if not isinstance(action, str) or action not in allowed:
        raise RequestError(403, 'Seu cargo não pode realizar esta ação.')
    expected_keys = {'action', 'revision', 'columns'} if action == 'EDIT' else {'action', 'revision', 'comment'} if action in ('COMMENT', 'REJECT', 'CANCEL') else {'action', 'revision'}
    if set(data) != expected_keys or type(data.get('revision')) is not int:
        raise RequestError(400, 'Campos da ação inválidos.')
    request = get_request(connection, request_id)
    if request is None:
        raise RequestError(404, 'Solicitação não encontrada.')
    if request['status'] != 'OPEN':
        raise RequestError(409, 'Esta solicitação já foi encerrada.')
    if request['revision'] != data['revision']:
        raise RequestError(409, 'A solicitação mudou. Atualize antes de decidir.')
    content = required_comment(data.get('comment')) if action in ('COMMENT', 'REJECT', 'CANCEL') else ''
    if action == 'EDIT':
        columns = request_columns(data['columns'])
        if len(columns) != len(request['columns']):
            raise RequestError(400, 'Edite somente nome e descrição; não adicione ou remova colunas do pedido.')
        check_request_columns(connection, request['tableId'], columns)
        connection.execute('UPDATE column_requests SET columns_json=? WHERE id=?', (json.dumps(columns, ensure_ascii=False), request_id))
        content = 'Colunas revisadas: ' + json.dumps(columns, ensure_ascii=False)
    elif action == 'APPROVE':
        check_request_columns(connection, request['tableId'], request['columns'])
        position = connection.execute('SELECT coalesce(max(position), -1) + 1 FROM table_columns WHERE table_id=?', (request['tableId'],)).fetchone()[0]
        connection.executemany('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)', [(request['tableId'], column['name'], column['description'], position + index) for index, column in enumerate(request['columns'])])
        content = 'Solicitação aprovada integralmente. Colunas adicionadas ao catálogo: ' + json.dumps(request['columns'], ensure_ascii=False)
    status = {'APPROVE': 'APPROVED', 'REJECT': 'REJECTED', 'CANCEL': 'CANCELLED'}.get(action, 'OPEN')
    connection.execute('UPDATE column_requests SET status=?,closed_at=?,revision=revision+1 WHERE id=?', (status, None if status == 'OPEN' else time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), request_id))
    record_request_action(connection, request_id, session, action, content)
    return get_request(connection, request_id)


def validated_script(data, schema, table):
    if not isinstance(data, dict) or set(data) != {'sql'}:
        raise ValueError('Envie somente o SQL.')
    sql = data['sql']
    if not isinstance(sql, str) or not 1 <= len(sql) <= 20000:
        raise ValueError('SQL deve conter de 1 a 20000 caracteres.')
    # Lexical envelope only: this is not a SQL dialect parser or an execution path.
    statements, tokens = [], []
    index = 0
    while index < len(sql):
        char = sql[index]
        if char.isspace():
            index += 1
            continue
        if sql.startswith('--', index) or char == '#':
            end = re.search(r'[\r\n]', sql[index:])
            index = index + end.start() if end else len(sql)
            continue
        if sql.startswith('/*', index):
            if sql.startswith(('/*!', '/*M!', '/*m!'), index):
                raise ValueError('Comentários executáveis não são permitidos.')
            end = sql.find('*/', index + 2)
            if end < 0 or '/*' in sql[index + 2:end]:
                raise ValueError('Comentário inválido.')
            index = end + 2
            continue
        if char == '$' and re.match(r'\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$', sql[index:]):
            raise ValueError('Dollar quotes não são suportados.')
        if char in "'\"`":
            quote, value = char, []
            index += 1
            while index < len(sql):
                char = sql[index]
                if char == quote:
                    if index + 1 < len(sql) and sql[index + 1] == quote:
                        value.append(quote)
                        index += 2
                        continue
                    index += 1
                    break
                if char == '\\':
                    if quote != "'" or index + 1 >= len(sql):
                        raise ValueError('Escape inválido.')
                    value.append(sql[index + 1])
                    index += 2
                    continue
                value.append(char)
                index += 1
            else:
                raise ValueError('String ou identificador não terminado.')
            tokens.append(('string' if quote == "'" else 'identifier', ''.join(value)))
            continue
        word = re.match(r'[A-Za-z_][A-Za-z0-9_$]*', sql[index:])
        if word:
            tokens.append(('word', word.group()))
            index += len(word.group())
        elif char == ';':
            if tokens:
                statements.append(tokens)
                tokens = []
            index += 1
        elif char in '.,()=+-*/%<>!|&:0123456789':
            tokens.append(('symbol', char))
            index += 1
        else:
            raise ValueError('Caractere SQL não suportado.')
    if tokens:
        statements.append(tokens)
    if not statements:
        raise ValueError('SQL sem comandos.')
    forbidden = {'CREATE', 'DELETE', 'TRUNCATE', 'SELECT', 'INSERT', 'UPDATE',
                 'TABLE', 'GRANT', 'REVOKE', 'CALL', 'EXEC', 'EXECUTE', 'USE'}
    actions = {'ADD', 'DROP', 'MODIFY', 'CHANGE', 'RENAME', 'ALTER', 'COMMENT',
               'ENGINE', 'CONVERT', 'DEFAULT', 'ENABLE', 'DISABLE'}
    for statement in statements:
        if (len(statement) < 7 or any(kind != 'word' for kind, _ in statement[:2])
                or [token[1].upper() for token in statement[:2]] != ['ALTER', 'TABLE']
                or statement[2][0] not in ('word', 'identifier')
                or statement[3] != ('symbol', '.')
                or statement[4][0] not in ('word', 'identifier')
                or statement[2][1].casefold() != schema.casefold()
                or statement[4][1].casefold() != table.casefold()):
            raise ValueError('Somente ALTER TABLE da tabela alvo é permitido.')
        action = statement[5:]
        if action[0][0] != 'word' or action[0][1].upper() not in actions:
            raise ValueError('Ação ALTER TABLE inválida.')
        if any(kind == 'word' and value.upper() in forbidden for kind, value in action):
            raise ValueError('Comando fora do envelope ALTER TABLE.')
        for position, (kind, value) in enumerate(action):
            if kind == 'word' and value.upper() == 'ALTER':
                if position + 1 >= len(action) or action[position + 1][0] != 'word' or action[position + 1][1].upper() != 'COLUMN':
                    raise ValueError('Somente ALTER COLUMN dentro da ação.')
        depth = 0
        clauses, clause = [], []
        for token in action:
            if token == ('symbol', '('):
                depth += 1
            elif token == ('symbol', ')'):
                depth -= 1
                if depth < 0:
                    raise ValueError('Parênteses inválidos.')
            if token == ('symbol', ',') and depth == 0:
                clauses.append(clause)
                clause = []
            else:
                clause.append(token)
        clauses.append(clause)
        if depth:
            raise ValueError('Parênteses inválidos.')
        for clause in clauses:
            if (len(clause) < 2 or clause[0][0] != 'word'
                    or clause[0][1].upper() not in actions
                    or clause[1][0] == 'symbol' and clause[1][1] != '='):
                raise ValueError('Ação não pode ser vazia.')
            operand = 1
            if clause[1][0] == 'word' and clause[1][1].upper() in {'COLUMN', 'CONSTRAINT', 'INDEX', 'KEY', 'TO', 'PRIMARY', 'FOREIGN'}:
                operand = 2
            if operand >= len(clause):
                raise ValueError('Ação sem operando.')
            if clause[0][1].upper() in {'ADD', 'DROP', 'MODIFY', 'CHANGE', 'ALTER', 'RENAME'}:
                if clause[operand][0] not in ('word', 'identifier') or not clause[operand][1]:
                    raise ValueError('Operando inválido.')
                if clause[0][1].upper() == 'ALTER' and operand + 1 >= len(clause):
                    raise ValueError('ALTER COLUMN sem ação.')
            if clause[1] == ('symbol', '=') and len(clause) < 3:
                raise ValueError('Ação sem valor.')
    return sql


def list_scripts(connection, table_id):
    return [dict(row) for row in connection.execute('''SELECT id, sql, created_at AS createdAt
        FROM scripts WHERE table_id=? ORDER BY created_at DESC, rowid DESC''', (table_id,))]


def password_matches(password, encoded):
    if encoded.startswith(('$2a$', '$2b$', '$2y$')):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), encoded.encode('ascii'))
        except (ImportError, ValueError, UnicodeEncodeError):
            return False
    _, salt, expected = encoded.split('$')
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(actual, bytes.fromhex(expected))


def write_connection(path):
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def validated_table(data):
    if not isinstance(data, dict) or set(data) - {'schema', 'name', 'description', 'columns'}:
        raise ValueError('Dados da tabela inválidos.')
    schema, name = data.get('schema'), data.get('name')
    identifier = r'[A-Za-z_][A-Za-z0-9_]{0,127}'
    if not isinstance(schema, str) or not isinstance(name, str) or not re.fullmatch(identifier, schema) or not re.fullmatch(identifier, name):
        raise ValueError('Schema e nome devem começar por letra ou _ e conter apenas letras, números e _.')
    description = data.get('description', '')
    columns = data.get('columns', [])
    if not isinstance(description, str) or len(description) > 4000 or not isinstance(columns, list) or len(columns) > 200:
        raise ValueError('Descrição ou quantidade de colunas inválida.')
    names = set()
    for column in columns:
        if not isinstance(column, dict) or set(column) - {'name', 'description'}:
            raise ValueError('Coluna inválida.')
        column_name = column.get('name')
        column_description = column.get('description', '')
        if not isinstance(column_name, str) or not re.fullmatch(identifier, column_name) or column_name.lower() in names:
            raise ValueError('Nomes de colunas inválidos ou repetidos.')
        if not isinstance(column_description, str) or len(column_description) > 4000:
            raise ValueError('Descrição da coluna inválida.')
        names.add(column_name.lower())
    return schema, name, description, columns


def read_connection(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.create_function("normalize", 1, normalize, deterministic=True)
    return connection


def list_tables(connection, query):
    return [dict(row) for row in connection.execute("""
        SELECT id, schema_name || '.' || name AS fullName, description
        FROM catalog_tables
        WHERE instr(normalize(schema_name || '.' || name), ?) > 0
        ORDER BY schema_name, name
    """, (normalize(query),))]


def get_table(connection, table_id):
    row = connection.execute("""
        SELECT id, schema_name || '.' || name AS fullName, description
        FROM catalog_tables WHERE id = ?
    """, (table_id,)).fetchone()
    if row is None:
        return None
    table = dict(row)
    table["columns"] = [dict(column) for column in connection.execute(
        "SELECT name, description FROM table_columns WHERE table_id = ? ORDER BY position", (table_id,)
    )]
    return table


def get_overview(connection):
    counts = connection.execute("""SELECT count(*) AS column_count,
        coalesce(sum(length(trim(description, char(9) || char(10) || char(13) || ' ')) > 0), 0)
        AS documented_count FROM table_columns""").fetchone()
    schemas = [dict(row) for row in connection.execute("""
        SELECT schema_name AS name, count(*) AS tableCount
        FROM catalog_tables GROUP BY schema_name ORDER BY schema_name
    """)]
    source = 'SQLite local'
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='xlsx_sources'").fetchone():
        sources = [row[0] for row in connection.execute('SELECT DISTINCT name FROM xlsx_sources ORDER BY name')]
        if sources:
            source += ' · XLSX: ' + ', '.join(sources)
    return {'tableCount': sum(schema['tableCount'] for schema in schemas),
            'columnCount': counts['column_count'], 'documentedColumnCount': counts['documented_count'],
            'schemas': schemas, 'source': source}


class CatalogHandler(BaseHTTPRequestHandler):
    server_version = "CatalogLocal"

    def send_payload(self, status, body, content_type="application/json; charset=utf-8", cookie=None, attachment=False):
        payload = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
        self.send_response(status)
        if cookie:
            self.send_header('Set-Cookie', cookie)
        if attachment:
            self.send_header('Content-Disposition', 'attachment')
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def valid_origin(self, required=False):
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').lower()
        if render_host:
            try:
                host_name = (urlsplit(f'//{host}').hostname or '').lower()
            except ValueError:
                host_name = ''
            expected_origin = (os.environ.get('APP_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL', '')).rstrip('/')
            host_allowed = host_name == render_host and expected_origin.startswith('https://')
        else:
            allowed_hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            expected_origin = f'http://{host}'
            host_allowed = host in allowed_hosts
        origin_allowed = origin == expected_origin if required else not origin or origin == expected_origin
        valid = host_allowed and origin_allowed
        if not valid:
            self.send_payload(403, {'error': 'Origem não permitida.'})
        return valid

    def session(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
        except CookieError:
            return None
        token = cookies.get('sid')
        if not token or len(token.value) > 128:
            return None
        digest = hashlib.sha256(token.value.encode()).hexdigest()
        with closing(read_connection(self.server.database)) as connection:
            row = connection.execute('''SELECT u.id,u.email,u.role,s.csrf_token,s.token_hash
                FROM sessions s JOIN users u ON u.id=s.user_id
                WHERE s.token_hash=? AND s.expires_at>?''', (digest, int(time.time()))).fetchone()
        return dict(row) if row else None

    def require_session(self):
        session = self.session()
        if not session:
            self.send_payload(401, {'error': 'Faça login para continuar.'})
        return session

    @staticmethod
    def public_session(session):
        return {'user': {key: session[key] for key in ('id','email','role')}, 'csrfToken': session['csrf_token']}

    def do_GET(self):
        if not self.valid_origin():
            return
        try:
            url = urlsplit(self.path)
            if url.scheme or url.netloc:
                self.send_payload(400, {"error": "Endereço inválido."})
                return
            path = unquote(url.path)
            if path == '/healthz' and not url.query:
                self.send_payload(200, {'ok': True})
                return
            if path in PUBLIC_FILES:
                name, content_type = PUBLIC_FILES[path]
                self.send_payload(200, (ROOT / name).read_bytes(), content_type)
                return
            if path == '/api/session':
                session = self.session()
                self.send_payload(200, self.public_session(session) if session else {'user': None})
                return
            if path in ('/api/overview', '/api/tables', '/api/documentations') or path.startswith(('/api/tables/', '/documentation-files/')):
                if not self.require_session():
                    return
            if path in ('/api/requests', '/api/notifications') or path.startswith('/api/requests/'):
                session = self.require_session()
                if not session:
                    return
                if session['role'] not in ('DBA', 'FULLSTACK'):
                    self.send_payload(403, {'error': 'Acesso restrito a DBA e FullStack.'})
                    return
                if url.query:
                    raise ValueError('Parâmetros inválidos.')
                with closing(read_connection(self.server.database)) as connection:
                    connection.execute('BEGIN')
                    if path == '/api/notifications':
                        notifications = [dict(row) for row in connection.execute('''SELECT id,request_id AS requestId,action,content,created_at AS createdAt,read_at AS readAt
                            FROM notifications WHERE user_id=? ORDER BY id DESC''', (session['id'],))]
                        data = {'notifications': notifications, 'unreadCount': sum(item['readAt'] is None for item in notifications)}
                    elif path == '/api/requests':
                        opened = connection.execute("SELECT id FROM column_requests WHERE status='OPEN' ORDER BY rowid DESC").fetchall()
                        closed = connection.execute("SELECT id FROM column_requests WHERE status IN ('APPROVED','REJECTED') ORDER BY closed_at DESC, (SELECT max(id) FROM request_actions WHERE request_id=column_requests.id) DESC LIMIT 5").fetchall()
                        data = {'open': [get_request(connection, row[0]) for row in opened], 'closed': [get_request(connection, row[0]) for row in closed]}
                    else:
                        request_id = path.removeprefix('/api/requests/')
                        if not request_id or '/' in request_id or len(request_id) > 128:
                            raise ValueError('Identificador inválido.')
                        data = get_request(connection, request_id)
                self.send_payload(200, data) if data is not None else self.send_payload(404, {'error': 'Solicitação não encontrada.'})
                return
            if path == '/api/documentations':
                if url.query:
                    self.send_payload(400, {'error': 'Parâmetros inválidos.'})
                    return
                with closing(read_connection(self.server.database)) as connection:
                    saved = connection.execute('SELECT schemas_json, documents_json FROM documentation_catalog WHERE id=1').fetchone()
                if saved:
                    data = {'schemas': json.loads(saved['schemas_json']), 'documents': json.loads(saved['documents_json'])}
                else:
                    data = json.loads((ROOT / 'documentations.json').read_text(encoding='utf-8'))
                self.send_payload(200, data)
                return
            if path.startswith('/documentation-files/'):
                relative = path.removeprefix('/documentation-files/')
                directory = (ROOT / 'documentation-files').resolve()
                original = (directory / relative).resolve()
                content_types = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '': 'text/plain; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/vnd.microsoft.icon', '.ttf': 'application/octet-stream'}
                for extension in ('.html', '.cjs', '.css', '.java', '.js', '.json', '.jsp', '.py', '.svg'):
                    content_types[extension] = 'text/plain; charset=utf-8'
                if url.query or not original.is_relative_to(directory) or not original.is_file() or original.suffix.lower() not in content_types:
                    self.send_payload(404, {'error': 'Arquivo não encontrado.'})
                    return
                self.send_payload(200, original.read_bytes(), content_types[original.suffix.lower()], attachment=original.suffix.lower() in ('.docx', '.ttf', '.html', '.svg'))
                return
            if path == '/api/overview':
                if url.query:
                    self.send_payload(400, {'error': 'Parâmetros inválidos.'})
                    return
                with closing(read_connection(self.server.database)) as connection:
                    connection.execute('BEGIN')
                    data = get_overview(connection)
                self.send_payload(200, data)
                return
            if path == "/api/tables":
                params = parse_qs(url.query, keep_blank_values=True, max_num_fields=4)
                if set(params) - {"q"} or len(params.get("q", [])) > 1:
                    self.send_payload(400, {"error": "Parâmetros inválidos."})
                    return
                query = params.get("q", [""])[0]
                if len(query) > 256:
                    self.send_payload(400, {"error": "A pesquisa deve ter no máximo 256 caracteres."})
                    return
                with closing(read_connection(self.server.database)) as connection:
                    data = list_tables(connection, query)
                self.send_payload(200, {"tables": data})
                return
            if path.startswith("/api/tables/"):
                script_route = path.endswith('/scripts')
                table_id = path.removeprefix("/api/tables/")
                if script_route:
                    table_id = table_id[:-len('/scripts')]
                if not table_id or "/" in table_id or len(table_id) > 128 or url.query:
                    self.send_payload(400, {"error": "Identificador ou parâmetros inválidos."})
                    return
                with closing(read_connection(self.server.database)) as connection:
                    connection.execute('BEGIN')
                    table = get_table(connection, table_id)
                    data = {'scripts': list_scripts(connection, table_id)} if script_route and table else table
                self.send_payload(200, data) if table else self.send_payload(404, {"error": "Tabela não encontrada."})
                return
            self.send_payload(404, {"error": "Recurso não encontrado."})
        except ValueError:
            self.send_payload(400, {"error": "Requisição inválida."})
        except (sqlite3.Error, OSError):
            logging.exception("Falha ao consultar catálogo local")
            self.send_payload(500, {"error": "Não foi possível consultar os dados. Tente novamente."})

    do_HEAD = do_GET

    def method_not_allowed(self):
        self.close_connection = True
        self.send_payload(405, {"error": "Somente consulta está disponível."})

    def read_json(self):
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            raise ValueError('Envie JSON válido.')
        length = int(self.headers.get('Content-Length', '0'))
        if not 0 < length <= 1048576:
            raise ValueError('Tamanho da requisição inválido.')
        self.connection.settimeout(5)
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError('Envie um objeto JSON.')
        return data

    def login(self, data):
        email, password = data.get('email'), data.get('password')
        if set(data) != {'email','password'} or not isinstance(email,str) or not isinstance(password,str) or len(email)>254 or not 1 <= len(password) <= 256:
            raise ValueError('E-mail ou senha inválidos.')
        ip = self.client_address[0]
        now = time.time()
        with self.server.auth_lock:
            failures = [stamp for stamp in self.server.login_failures.get(ip, []) if now-stamp < 60]
            self.server.login_failures[ip] = failures
            if len(failures) >= 10:
                self.send_payload(429, {'error': 'Muitas tentativas. Aguarde um minuto.'})
                return
            failures.append(now)
        with closing(read_connection(self.server.database)) as connection:
            user = connection.execute('SELECT * FROM users WHERE email=?', (email.strip().lower(),)).fetchone()
            dummy_hash = connection.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0]
        valid = password_matches(password, user['password_hash'] if user else dummy_hash)
        if not user or not valid:
            self.send_payload(401, {'error': 'E-mail ou senha inválidos.'})
            return
        with self.server.auth_lock:
            self.server.login_failures.pop(ip, None)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        previous = self.session()
        with closing(write_connection(self.server.database)) as connection, connection:
            connection.execute('DELETE FROM sessions WHERE expires_at<=?', (int(now),))
            if previous:
                connection.execute('DELETE FROM sessions WHERE token_hash=?', (previous['token_hash'],))
            connection.execute('INSERT INTO sessions VALUES (?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user['id'], csrf, int(now)+28800))
        result = {'user': {key:user[key] for key in ('id','email','role')}, 'csrfToken':csrf}
        secure = '; Secure' if (os.environ.get('APP_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL', '')).startswith('https://') else ''
        self.send_payload(200, result, cookie=f'sid={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}')

    def change_column(self, table_id):
        data = self.read_json()
        adding = self.command == 'POST'
        if set(data) - ({'name', 'description'} if adding else {'name'}):
            raise ValueError('Campos de coluna inválidos.')
        name = data.get('name')
        if (not isinstance(name, str) or not name.strip()
                or adding and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', name)):
            self.send_payload(400, {'error': 'Nome de coluna inválido. Use letras, números e sublinhado, começando com letra ou sublinhado.'})
            return
        description = data.get('description', '')
        if adding and (not isinstance(description, str) or len(description) > 4000):
            raise ValueError('Descrição de coluna inválida.')
        with closing(write_connection(self.server.database)) as connection, connection:
            connection.execute('BEGIN IMMEDIATE')
            if not connection.execute('SELECT 1 FROM catalog_tables WHERE id=?', (table_id,)).fetchone():
                self.send_payload(404, {'error': 'Tabela não encontrada.'})
                return
            if adding:
                if connection.execute('SELECT 1 FROM table_columns WHERE table_id=? AND name=? COLLATE NOCASE', (table_id, name)).fetchone():
                    self.send_payload(409, {'error': 'Já existe uma coluna com esse nome.'})
                    return
                count, position = connection.execute('SELECT count(*), coalesce(max(position), -1) + 1 FROM table_columns WHERE table_id=?', (table_id,)).fetchone()
                if count >= 200:
                    raise ValueError('A tabela já possui 200 colunas.')
                connection.execute('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)', (table_id, name, description, position))
            else:
                deleted = connection.execute('DELETE FROM table_columns WHERE table_id=? AND name=?', (table_id, name))
                if not deleted.rowcount:
                    self.send_payload(404, {'error': 'Não foi possível excluir: a coluna não existe nesta tabela. Atualize a página.'})
                    return
            table = get_table(connection, table_id)
        self.send_payload(201 if adding else 200, table)

    def add_script(self, table_id):
        data = self.read_json()
        with closing(write_connection(self.server.database)) as connection, connection:
            connection.execute('BEGIN IMMEDIATE')
            table = connection.execute('SELECT schema_name, name FROM catalog_tables WHERE id=?', (table_id,)).fetchone()
            if table is None:
                self.send_payload(404, {'error': 'Tabela não encontrada.'})
                return
            try:
                sql = validated_script(data, table['schema_name'], table['name'])
            except ValueError:
                self.send_payload(400, {'error': 'Script inválido. Revise o comando ALTER TABLE e a tabela informada.'})
                return
            connection.execute('INSERT INTO scripts(id, table_id, sql, created_at) VALUES (?,?,?,?)',
                (secrets.token_hex(16), table_id, sql, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
            scripts = list_scripts(connection, table_id)
        self.send_payload(201, {'scripts': scripts})

    def delete_table(self, table_id):
        data = self.read_json()
        if (set(data) != {'confirmation', 'confirmed'}
                or data['confirmation'] != 'DELeT@R' or data['confirmed'] is not True):
            raise ValueError('Confirme a exclusão com DELeT@R e confirmed=true.')
        with closing(write_connection(self.server.database)) as connection, connection:
            connection.execute('BEGIN IMMEDIATE')
            if connection.execute('SELECT 1 FROM column_requests WHERE table_id=? LIMIT 1', (table_id,)).fetchone():
                raise RequestError(409, 'Tabela com histórico de solicitações não pode ser excluída.')
            deleted = connection.execute('DELETE FROM catalog_tables WHERE id=?', (table_id,))
            if not deleted.rowcount:
                self.send_payload(404, {'error': 'Tabela não encontrada.'})
                return
        self.send_payload(200, {'ok': True})

    def do_DELETE(self):
        url = urlsplit(self.path)
        path = unquote(url.path)
        if path.startswith('/api/tables/') and not path.endswith('/scripts'):
            self.do_POST()
        else:
            self.method_not_allowed()

    def do_POST(self):
        if not self.valid_origin(required=True):
            return
        try:
            url = urlsplit(self.path)
            if url.scheme or url.netloc or url.query:
                raise ValueError('Endereço inválido.')
            path = unquote(url.path)
            column_route = path.startswith('/api/tables/') and path.endswith('/columns')
            script_route = path.startswith('/api/tables/') and path.endswith('/scripts')
            table_route = self.command == 'DELETE' and path.startswith('/api/tables/') and not column_route and not script_route
            documentation_route = path == '/api/documentations'
            suffix = '/scripts' if script_route else '/columns'
            table_id = path[len('/api/tables/'):-len(suffix)] if column_route or script_route else path[len('/api/tables/'):] if table_route else None
            if (column_route or script_route or table_route) and (not table_id or '/' in table_id or len(table_id) > 128):
                raise ValueError('Identificador inválido.')
            request_route = path == '/api/requests' or path.startswith('/api/requests/')
            notification_route = path == '/api/notifications/read'
            if not column_route and not script_route and not table_route and not request_route and not notification_route and not documentation_route and path not in ('/api/login','/api/logout','/api/tables'):
                self.send_payload(404, {'error':'Recurso não encontrado.'})
                return
            if path == '/api/login':
                self.login(self.read_json())
                return
            session = self.require_session()
            if not session:
                return
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token','').encode(), session['csrf_token'].encode()):
                self.send_payload(403, {'error':'Sessão de formulário inválida. Atualize a página.'})
                return
            if path == '/api/logout':
                with closing(write_connection(self.server.database)) as connection, connection:
                    connection.execute('DELETE FROM sessions WHERE token_hash=?', (session['token_hash'],))
                secure = '; Secure' if (os.environ.get('APP_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL', '')).startswith('https://') else ''
                self.send_payload(200, {'ok':True}, cookie=f'sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0{secure}')
                return
            if request_route or notification_route:
                if session['role'] not in ('DBA', 'FULLSTACK'):
                    raise RequestError(403, 'Acesso restrito a DBA e FullStack.')
                data = self.read_json()
                with closing(write_connection(self.server.database)) as connection, connection:
                    connection.execute('BEGIN IMMEDIATE')
                    if notification_route:
                        if set(data) != {'id'} or type(data['id']) is not int:
                            raise RequestError(400, 'Notificação inválida.')
                        changed = connection.execute('UPDATE notifications SET read_at=coalesce(read_at, ?) WHERE id=? AND user_id=?', (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), data['id'], session['id']))
                        if not changed.rowcount:
                            raise RequestError(404, 'Notificação não encontrada.')
                        result = {'ok': True}
                    else:
                        request_id = path.removeprefix('/api/requests/') if path != '/api/requests' else None
                        if request_id is not None and (not request_id or '/' in request_id or len(request_id) > 128):
                            raise RequestError(400, 'Identificador inválido.')
                        result = mutate_request(connection, session, request_id, data)
                self.send_payload(201 if request_route and path == '/api/requests' else 200, result)
                return
            if documentation_route:
                if session['role'] != 'DBA':
                    self.send_payload(403, {'error': 'Somente DBA pode alterar as documentações do catálogo.'})
                    return
                schemas, documents = validated_documentation_catalog(self.read_json())
                timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                with closing(write_connection(self.server.database)) as connection, connection:
                    connection.execute('''INSERT INTO documentation_catalog(id,schemas_json,documents_json,updated_at)
                        VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET
                        schemas_json=excluded.schemas_json, documents_json=excluded.documents_json,
                        updated_at=excluded.updated_at''',
                        (json.dumps(schemas, ensure_ascii=False), json.dumps(documents, ensure_ascii=False), timestamp))
                self.send_payload(200, {'schemas': schemas, 'documents': documents})
                return
            if table_route:
                if session['role'] != 'DBA':
                    self.send_payload(403, {'error': 'Somente DBA pode excluir tabelas locais.'})
                    return
                self.delete_table(table_id)
                return
            if script_route:
                if session['role'] != 'DBA':
                    self.send_payload(403, {'error': 'Somente DBA pode documentar scripts.'})
                    return
                self.add_script(table_id)
                return
            if column_route:
                if session['role'] != 'DBA':
                    self.send_payload(403, {'error': 'Somente DBA pode adicionar ou remover colunas.'})
                    return
                self.change_column(table_id)
                return
            if session['role'] != 'DBA':
                self.send_payload(403, {'error':'Somente DBA pode criar tabelas.'})
                return
            schema, name, description, columns = validated_table(self.read_json())
            table_id = secrets.token_hex(16)
            with closing(write_connection(self.server.database)) as connection, connection:
                connection.execute('INSERT INTO catalog_tables VALUES (?,?,?,?)', (table_id,schema,name,description))
                connection.executemany('INSERT INTO table_columns(table_id,name,description,position) VALUES (?,?,?,?)', [(table_id,column['name'],column.get('description',''),position) for position,column in enumerate(columns)])
            with closing(read_connection(self.server.database)) as connection:
                self.send_payload(201, get_table(connection, table_id))
        except RequestError as error:
            self.send_payload(error.status, {'error': error.message})
        except (ValueError, UnicodeError):
            self.close_connection = True
            self.send_payload(400, {'error':'Dados inválidos. Verifique os campos e o formato JSON.'})
        except sqlite3.IntegrityError:
            self.send_payload(409, {'error':'Já existe uma tabela com esse schema e nome.'})
        except (sqlite3.Error, OSError):
            logging.exception('Falha no catálogo local')
            self.close_connection = True
            self.send_payload(500, {'error':'Não foi possível concluir a operação.'})

    do_PUT = do_PATCH = do_OPTIONS = method_not_allowed


def create_server(database, port=8765, host='127.0.0.1'):
    server = ThreadingHTTPServer((host, port), CatalogHandler)
    server.database = Path(database).resolve()
    server.auth_lock = threading.Lock()
    server.login_failures = {}
    return server


def import_production_catalog(database):
    from import_catalog import import_catalog

    database = Path(database)
    workbook = ROOT / 'Tracking - Mottainai - Operacional e Analitico - Centralizado.xlsx'
    report = import_catalog(database, workbook)
    for backup in database.parent.glob(database.stem + '.pre-xlsx-*.sqlite3'):
        backup.unlink(missing_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser(description="Catálogo Mottainai Hub com autenticação e permissões por perfil.")
    parser.add_argument("--host", default=os.environ.get('HOST', '127.0.0.1'))
    parser.add_argument("--port", type=int, default=int(os.environ.get('PORT', '8765')))
    parser.add_argument("--database", type=Path, default=Path(os.environ.get('CATALOG_DB_PATH', str(ROOT / "catalog.sqlite3"))))
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    fresh_database = not args.database.exists()
    initialize_database(args.database)
    if fresh_database and os.environ.get('APP_ENV', '').lower() == 'production':
        import_production_catalog(args.database)
    with create_server(args.database, args.port, args.host) as server:
        print(f"Motta-hub ouvindo em {args.host}:{server.server_port}", flush=True)
        print(f"Banco SQLite: {args.database.resolve()}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
