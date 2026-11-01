# 09 — Auditoria e Observabilidade

Camada **transversal** que garante rastreabilidade, monitoramento e governança: auditoria de operações, logs, fila de eventos, jobs, KPIs em cache, histórico de mudanças e versionamento de schema.

## `schema_version`

Registro de versões aplicadas ao banco (fonte do `install.sql`).

| Coluna | Tipo | Restrições |
|---|---|---|
| `version_id` 🔑 | `BIGSERIAL` | `PK` |
| `version` 🔎 | `VARCHAR(20)` | `NN` `UQ` |
| `description` | `VARCHAR(200)` | `NN` |
| `type` | `migration_type` (enum) | `NN` `def SQL` |
| `script` | `VARCHAR(100)` | `NN` |
| `checksum` | `VARCHAR(64)` | |
| `installed_by` | `VARCHAR(100)` | `NN` |
| `installed_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `execution_time` | `INTEGER` | ms de execução |
| `success` | `BOOLEAN` | `NN` `def TRUE` |

**Índices:** `idx_schema_version_version`, `idx_schema_version_installed_at`.

## `audit_log`

Trilha de auditoria de operações sensíveis. **Tabela particionada por `operation_date`** (PK composta).

| Coluna | Tipo | Restrições |
|---|---|---|
| `audit_id` 🔑 | `BIGINT` identity | parte da `PK (audit_id, operation_date)` |
| `table_affected` | `VARCHAR(60)` | `NN` |
| `operation` | `audit_operation` (enum) | `NN` (INSERT / UPDATE / DELETE) |
| `record_id` | `TEXT` | `NN` linha afetada |
| `user_id` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `old_data` / `new_data` | `JSONB` | estados anterior/novo |
| `operation_date` 🔑 | `TIMESTAMP` | parte da PK · coluna de partição · `def NOW()` |
| `company_id` | `INTEGER` | tenant do contexto |
| `store_id` | `INTEGER` | loja do contexto |
| `client_ip` | `INET` | origem observada pelo PostgreSQL |
| `application_name` | `VARCHAR(100)` | cliente declarado na conexão |
| `transaction_id` | `BIGINT` | correlação forense da transação |

**Preenchimento:** triggers cobrem logística, funcionários, contas, clientes, consentimentos, tokens, sessões, compras, vendas e movimentações. A função sanitiza recursivamente documentos, identificadores e hashes antes de gravar. `mottainai_api` possui somente leitura filtrada por empresa; `mottainai_customer_api` não acessa a auditoria. Nenhuma role de API pode inserir, alterar, excluir ou truncar auditoria. Particionamento é mensal.

## `legacy_sync_record`

Trilha idempotente da transferência entre os dois bancos físicos. Guarda
origem, identificadores técnicos, destino, status, instante e SHA-256 do
payload já tratado. O payload bruto não é persistido e a role do cliente não
possui acesso.

## `system_log`

Logs operacionais gerais do sistema.

| Coluna | Tipo | Restrições |
|---|---|---|
| `log_id` 🔑 | `BIGSERIAL` | `PK` |
| `log_level` | `log_level` (enum) | `NN` (DEBUG / INFO / WARN / ERROR / FATAL) |
| `module` | `VARCHAR(50)` | |
| `message` | `TEXT` | `NN` |
| `stack_trace` | `TEXT` | |
| `user_id` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `ip_address` | `INET` | |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `error_log`

Registro estruturado de erros/exceções (também usado pelos triggers de lote/FEFO em falha).

| Coluna | Tipo | Restrições |
|---|---|---|
| `error_id` 🔑 | `BIGSERIAL` | `PK` |
| `error_code` | `VARCHAR(20)` | |
| `error_message` | `TEXT` | `NN` |
| `function_name` | `VARCHAR(100)` | |
| `parameters` | `JSONB` | |
| `stack_trace` | `TEXT` | |
| `user_id` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `integration_log`

Logs de integrações com sistemas externos (fiscal, pagamentos, providers).

| Coluna | Tipo | Restrições |
|---|---|---|
| `integration_id` 🔑 | `BIGSERIAL` | `PK` |
| `integration_type` | `VARCHAR(50)` | `NN` |
| `direction` | `VARCHAR(10)` | `NN` |
| `payload` / `response` | `JSONB` | |
| `status` | `VARCHAR(20)` | `NN` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

> Sem FKs — registro assíncrono desacoplado do fluxo transacional.

## `job_log`

Controle de execução de jobs/automações.

| Coluna | Tipo | Restrições |
|---|---|---|
| `job_id` 🔑 | `BIGSERIAL` | `PK` |
| `company_id` 🔗 | `INTEGER` | `FK → company(company_id) ON DELETE RESTRICT`; nulo apenas para registros globais legados |
| `job_name` | `VARCHAR(100)` | `NN` |
| `job_type` | `VARCHAR(50)` | |
| `start_time` | `TIMESTAMP` | `NN` |
| `end_time` | `TIMESTAMP` | |
| `duration_seconds` | `INTEGER` | |
| `records_processed` | `INTEGER` | |
| `success` | `BOOLEAN` | |
| `details` | `JSONB` | |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## Históricos de mudança

Três tabelas de histórico gravam alterações de cadastro/custo ao longo do tempo (ver triggers em `06_triggers.sql`).

### `product_history`

Histórico de alterações de cadastro de produto (trigger `trg_product_history`).

| Coluna | Tipo | Restrições |
|---|---|---|
| `history_id` 🔑 | `BIGSERIAL` | `PK` |
| `product_id` 🔗 | `INTEGER` | `FK → product(product_id) ON DELETE CASCADE` |
| `field_name` | `VARCHAR(50)` | `NN` |
| `old_value` / `new_value` | `TEXT` | |
| `changed_by` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `changed_at` | `TIMESTAMP` | `NN` `def NOW()` |

### `supplier_history`

Histórico de alterações de fornecedor.

| Coluna | Tipo | Restrições |
|---|---|---|
| `history_id` 🔑 | `BIGSERIAL` | `PK` |
| `supplier_id` 🔗 | `INTEGER` | `FK → supplier(supplier_id) ON DELETE CASCADE` |
| `field_name` | `VARCHAR(50)` | `NN` |
| `old_value` / `new_value` | `TEXT` | |
| `changed_by` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `changed_at` | `TIMESTAMP` | `NN` `def NOW()` |

### `product_price_history`

Histórico de preços (resultado do cálculo de custo médio e preço sugerido — RF16, via `trg_batch_update_cost`).

| Coluna | Tipo | Restrições |
|---|---|---|
| `price_history_id` 🔑 | `BIGSERIAL` | `PK` |
| `product_id` 🔗 | `INTEGER` | `FK → product(product_id) ON DELETE CASCADE` |
| `old_price` / `new_price` | `DECIMAL(10,2)` | |
| `changed_by` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `changed_at` | `TIMESTAMP` | `NN` `def NOW()` |

## Fila e cache

### `event_queue`

Fila de eventos assíncronos para processamento posterior.

| Coluna | Tipo | Restrições |
|---|---|---|
| `event_id` 🔑 | `BIGSERIAL` | `PK` |
| `event_type` | `VARCHAR(50)` | `NN` |
| `event_data` | `JSONB` | `NN` |
| `priority` | `INTEGER` | `def 5` |
| `status` | `event_status` (enum) | `NN` `def PENDING` |
| `created_at` | `TIMESTAMP` | `def NOW()` |
| `processed_at` | `TIMESTAMP` | |
| `retry_count` | `INTEGER` | `def 0` |
| `error_message` | `TEXT` | |
| `company_id` | `INTEGER` | tenant do evento, quando aplicável |

`fn_find_outbox_event_by_key` permite localizar uma publicação anterior pela
chave de idempotência. As views de monitoramento não expõem jobs globais com
`company_id IS NULL` à API.

**Índices:** `idx_event_queue_status (status, priority)`, `idx_event_queue_created (created_at)`.

### `kpi_cache`

Indicadores **pré-calculados** (cache) para dashboards, com expiração.

| Coluna | Tipo | Restrições |
|---|---|---|
| `cache_id` 🔑 | `BIGSERIAL` | `PK` |
| `store_id` 🔗 | `INTEGER` | `FK → retail_store(store_id) ON DELETE CASCADE` |
| `kpi_name` | `VARCHAR(50)` | `NN` |
| `kpi_value` | `JSONB` | `NN` |
| `calculated_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `expires_at` | `TIMESTAMP` | `NN` |
| 🔎 `UQ` | | `(store_id, kpi_name)` |

**Índice:** `idx_kpi_cache_expires (expires_at)`.

### `query_performance`

Estatísticas de performance de consultas/funções (observabilidade de banco).

| Coluna | Tipo | Restrições |
|---|---|---|
| `performance_id` 🔑 | `BIGSERIAL` | `PK` |
| `function_name` | `VARCHAR(100)` | `NN` |
| `execution_time_ms` | `INTEGER` | `NN` |
| `rows_affected` | `INTEGER` | |
| `parameters` | `JSONB` | |
| `executed_at` | `TIMESTAMP` | `NN` `def NOW()` |

**Índices:** `idx_query_performance_executed (executed_at)`, `idx_query_performance_function (function_name)`.

## Arquivos de arquivamento (`*_archive`)

Tabelas de arquivamento criadas por **`CREATE TABLE … (LIKE <origem>)`**, duplicando a estrutura de colunas da tabela base (sem partições):

| Tabela arquivo | Origem clonada |
|---|---|
| `audit_log_archive` | `LIKE audit_log` |
| `inventory_movement_archive` | `LIKE inventory_movement` |
| `sales_transaction_archive` | `LIKE sales_transaction` |

> **Papel:** preservar dados históricos fora das partições ativas (retenção), mantendo a estrutura de colunas idêntica à origem.

---

*Próximo: [10 — Camada Analítica](10-camada-analitica.md)*
