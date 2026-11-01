# 05 — Vendas e PDV

Domínio da **frente de caixa**: cliente, terminais, turnos, movimentação de caixa, a venda em si, seus itens e pagamentos, o documento fiscal e as solicitações de cancelamento com aprovação.

```
customer ── 1:N ── customer_consent
customer ── 1:0..1 ── customer_private_data
customer ── 1:N ── sales_transaction  (customer_id SET NULL)
store ──< pos_terminal ──< pos_shift ──< pos_cash_movement
store ──< sales_transaction (particionada por sale_date)
sales_transaction ──< sale_item ──> batch (FEFO)
sales_transaction ──< sale_payment
sales_transaction ── 1:1 ── fiscal_document
sales_transaction ──< pos_cancel_request
```

## `customer`

Consumidor final. Registro **modal** — a venda pode ocorrer sem cliente identificado.

| Coluna | Tipo | Restrições |
|---|---|---|
| `customer_id` 🔑 | `INTEGER` identity | `PK` |
| `full_name` | `VARCHAR(150)` | `NN`; token `CUS_SHA256_*` |
| `cpf` 🔎 | `VARCHAR(80)` | `UQ` nullable; token `CPF_SHA256_*` |
| `email` | `VARCHAR(150)` | token `EMAIL_SHA256_*` nullable |
| `phone` | `VARCHAR(80)` | token `PHONE_SHA256_*` nullable |
| `address_id` | `INTEGER` | deve permanecer nulo; cliente não referencia endereço aberto |
| `address_token` | `VARCHAR(80)` | token `ADDR_SHA256_*` nullable |
| `external_auth_uid` 🔎 | `VARCHAR(150)` | `UQ`; token `AUTH_SHA256_*` |
| `birth_year` | `SMALLINT` | dado minimizado; a data exata não existe |
| `data_protection_version` | `SMALLINT` | `NN` `def 1` |
| `marketing_consent` | `BOOLEAN` | `NN` `def FALSE` |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |

## `customer_private_data`

Envelope opcional e recuperável dos dados pessoais autorizados. Há no máximo um
envelope por cliente e a chave AES nunca é armazenada no PostgreSQL.

| Coluna | Tipo | Restrições |
|---|---|---|
| `customer_id` 🔑 | `INTEGER` | `PK`, `FK → customer(customer_id) ON DELETE RESTRICT` |
| `payload_ciphertext` | `BYTEA` | `NN`; JSON_V1 cifrado e autenticado com AES-256-GCM |
| `payload_nonce` | `BYTEA` | `NN`, exatamente 12 bytes e único |
| `key_version` | `SMALLINT` | `NN`, positivo; identifica a chave externa |
| `algorithm` | `VARCHAR(20)` | `NN`, `AES-256-GCM` |
| `payload_format` | `VARCHAR(20)` | `NN`, `JSON_V1` |
| `encrypted_at` | `TIMESTAMPTZ` | `NN` |
| timestamps | `TIMESTAMPTZ` | `created_at`, `updated_at`, `deleted_at` |

**Segurança:** RLS forçada, ciphertext e nonce redigidos da auditoria, leitura
mobile limitada ao próprio cliente e leitura interna limitada a
gerente/administrador da empresa que realizou uma venda para o cliente.
Exclusões são lógicas; as APIs não recebem privilégio `DELETE`.

## `customer_auth`

Credenciais e controle de acesso do cliente (1:1 com `customer`).

| Coluna | Tipo | Restrições |
|---|---|---|
| `customer_auth_id` 🔑 | `INTEGER` identity | `PK` |
| `customer_id` 🔗 | `INTEGER` | `NN` `UQ` `FK → customer(customer_id) ON DELETE CASCADE` |
| `login_email` 🔎 | `VARCHAR(150)` | `NN` `UQ`; token `EMAIL_SHA256_*` |
| `password_hash` | `TEXT` | `NN`; BCrypt |
| `password_changed_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `failed_attempts` ✅ | `INTEGER` | `NN` `def 0` `CHECK ≥ 0` |
| `locked_until` | `TIMESTAMP` | bloqueio por tentativas |
| `recovery_token_hash` / `recovery_expires_at` | `TEXT` / `TIMESTAMP` | BCrypt e expiração; ambos nulos ou preenchidos |
| `last_login_at` | `TIMESTAMP` | |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `(recovery_token_hash IS NULL AND recovery_expires_at IS NULL) OR (recovery_token_hash IS NOT NULL AND recovery_expires_at IS NOT NULL)` |

## `customer_consent`

Histórico versionado de decisões do titular, sem armazenar dado pessoal aberto.

| Coluna | Tipo | Restrições |
|---|---|---|
| `customer_consent_id` 🔑 | `BIGINT` identity | `PK` |
| `customer_id` 🔗 | `INTEGER` | `NN` `FK → customer ON DELETE CASCADE` |
| `consent_type` | `VARCHAR(40)` | política, marketing, geolocalização ou fidelidade |
| `granted` | `BOOLEAN` | `NN` |
| `policy_version` | `VARCHAR(40)` | `NN` |
| `collection_channel` | `VARCHAR(30)` | app, web, suporte ou migração |
| `recorded_at` / `withdrawn_at` | `TIMESTAMPTZ` | histórico de concessão ou retirada |

**Segurança:** RLS limita leitura e escrita ao cliente autenticado; alterações são auditadas.

## `pos_terminal`

Equipamento/terminal de caixa de uma loja.

| Coluna | Tipo | Restrições |
|---|---|---|
| `terminal_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `terminal_code` | `VARCHAR(30)` | `NN` |
| `name` | `VARCHAR(80)` | `NN` |
| `hostname` | `VARCHAR(120)` | |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| 🔎 `UQ` | | `(store_id, terminal_code)` |

## `pos_shift`

Turno de abertura/fechamento do caixa (controle de sangrias e segurança). Índices únicos parciais garantem **um único turno aberto** por terminal e por funcionário.

| Coluna | Tipo | Restrições |
|---|---|---|
| `shift_id` 🔑 | `INTEGER` identity | `PK` |
| `terminal_id` 🔗 | `INTEGER` | `NN` `FK → pos_terminal(terminal_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `opened_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `opening_amount` ✅ | `DECIMAL(12,2)` | `NN` `def 0` `CHECK ≥ 0` |
| `closed_at` | `TIMESTAMP` | |
| `closing_amount` ✅ | `DECIMAL(12,2)` | `CHECK NULL OU ≥ 0` |
| `expected_amount` ✅ | `DECIMAL(12,2)` | |
| `status` ✅ | `VARCHAR(20)` | `NN` `def OPEN` `CHECK IN ('OPEN','CLOSED','CANCELED')` |
| `observation` | `TEXT` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `closed_at IS NULL OR closed_at ≥ opened_at` |

**Índices únicos parciais:** `idx_pos_shift_one_open_terminal (terminal_id) WHERE status='OPEN'`; `idx_pos_shift_one_open_employee (employee_id) WHERE status='OPEN'`.

## `pos_cash_movement`

Movimentação de caixa dentro de um turno (sangria/reforço).

| Coluna | Tipo | Restrições |
|---|---|---|
| `cash_movement_id` 🔑 | `INTEGER` identity | `PK` |
| `shift_id` 🔗 | `INTEGER` | `NN` `FK → pos_shift(shift_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `movement_type` ✅ | `VARCHAR(12)` | `NN` `CHECK IN ('SANGRIA','SUPRIMENTO')` |
| `amount` ✅ | `DECIMAL(12,2)` | `NN` `CHECK > 0` |
| `movement_date` | `TIMESTAMP` | `NN` `def NOW()` |
| `reason` | `VARCHAR(200)` | `NN` |
| `observation` | `TEXT` | |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `sales_transaction`

Transação comercial (o "cupom"). **Tabela particionada por `sale_date`** (PK composta).

| Coluna | Tipo | Restrições |
|---|---|---|
| `sale_id` 🔑 | `INTEGER` identity | parte da `PK (sale_id, sale_date)` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `shift_id` 🔗 | `INTEGER` | `NN` `FK → pos_shift(shift_id) ON DELETE RESTRICT` |
| `customer_id` 🔗 | `INTEGER` | `FK → customer(customer_id) ON DELETE SET NULL` (opcional) |
| `customer_document` ✅ | `VARCHAR(80)` | token `DOC_SHA256_*` nullable; nunca CPF/CNPJ aberto |
| `sale_date` 🔑 | `TIMESTAMP` | parte da PK · coluna de partição · `def NOW()` |
| `total_amount` ✅ | `DECIMAL(12,2)` | `NN` `def 0` `CHECK ≥ 0` |
| `status` | `sale_status` (enum) | `NN` `def COMPLETED` |
| `observation` | `TEXT` | |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |

**Observações:** sujeita a **RLS** (`sales_policy`). `idx_sales_store_status_date (store_id, status, sale_date)`, `idx_sales_customer_id`, `idx_sales_shift_id`.

## `sale_item`

Item vendido; o **lote** é selecionado automaticamente por **FEFO** no insert (trigger `trg_select_batch_fefo`).

| Coluna | Tipo | Restrições |
|---|---|---|
| `sale_item_id` 🔑 | `INTEGER` identity | `PK` |
| `sale_id` 🔗 | `INTEGER` | `NN` `FK (sale_id, sale_date) → sales_transaction … ON DELETE CASCADE` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(product_id) ON DELETE RESTRICT` |
| `batch_id` 🔗 | `INTEGER` | `FK → batch(batch_id) ON DELETE SET NULL` |
| `quantity_sold` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `unit_price` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `status` | `sale_item_status` (enum) | `NN` `def SOLD` |
| `canceled_at` | `TIMESTAMP` | |
| `subtotal` | `DECIMAL(12,2)` | **gerado** — `(quantity_sold * unit_price) STORED` |
| `sale_date` 🔗 | `TIMESTAMP` | `NN` (parte da FK composta) |
| `created_at` | `TIMESTAMP` | `def NOW()` |

**Trigger:** `trg_select_batch_fefo` — antes do insert, seleciona o lote de menor validade e valida cobertura de estoque.

**Índices:** `idx_sale_item_sale_id`, `idx_sale_item_product_id`, `idx_sale_item_batch_id`.

## `sale_payment`

Forma de pagamento de uma venda (dinheiro, cartão, PIX, boleto), com dados do adquirente.

| Coluna | Tipo | Restrições |
|---|---|---|
| `sale_payment_id` 🔑 | `INTEGER` identity | `PK` |
| `sale_id` 🔗 | `INTEGER` | `NN` `FK (sale_id, sale_date) → sales_transaction … ON DELETE CASCADE` |
| `sale_date` 🔗 | `TIMESTAMP` | `NN` (parte da FK composta) |
| `payment_method` | `payment_method` (enum) | `NN` |
| `amount` ✅ | `DECIMAL(12,2)` | `NN` `CHECK > 0` |
| `installments` ✅ | `INTEGER` | `NN` `def 1` `CHECK > 0` |
| `authorization_code` | `VARCHAR(100)` | |
| `nsu` | `VARCHAR(100)` | |
| `transaction_id` | `VARCHAR(150)` | referência do adquirente |
| `paid_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `fiscal_document`

Documento fiscal emitido para a venda (NF-e / NFC-e / SAT), relação 1:1.

| Coluna | Tipo | Restrições |
|---|---|---|
| `fiscal_document_id` 🔑 | `INTEGER` identity | `PK` |
| `sale_id` 🔗 | `INTEGER` | `NN` `FK (sale_id, sale_date) → sales_transaction … ON DELETE RESTRICT` |
| `sale_date` 🔗 | `TIMESTAMP` | `NN` (parte da FK composta) |
| `document_type` ✅ | `VARCHAR(10)` | `NN` `CHECK IN ('NFE','NFCE','SAT')` |
| `series` | `VARCHAR(10)` | |
| `document_number` | `VARCHAR(30)` | |
| `access_key` 🔎 | `VARCHAR(44)` | `UQ` (nullable) `CHECK NULL OU ^\d{44}$` |
| `status` ✅ | `VARCHAR(20)` | `NN` `def AUTHORIZED` `CHECK IN ('PENDING','AUTHORIZED','CANCELED','REJECTED')` |
| `issued_at` | `TIMESTAMP` | |
| `total_amount` ✅ | `DECIMAL(12,2)` | `NN` `def 0` `CHECK ≥ 0` |
| `protocol_number` | `VARCHAR(100)` | |
| `xml_content` | `TEXT` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

## `pos_cancel_request`

Solicitação de cancelamento de venda ou item — **exige fluxo de decisão** (aprovador).

| Coluna | Tipo | Restrições |
|---|---|---|
| `cancel_request_id` 🔑 | `INTEGER` identity | `PK` |
| `sale_id` 🔗 | `INTEGER` | `NN` `FK (sale_id, sale_date) → sales_transaction … ON DELETE RESTRICT` |
| `sale_date` 🔗 | `TIMESTAMP` | `NN` (parte da FK composta) |
| `sale_item_id` 🔗 | `INTEGER` | `FK → sale_item(sale_item_id) ON DELETE RESTRICT` |
| `requested_by` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `approved_by` 🔗 | `INTEGER` | `FK → employee(employee_id) ON DELETE RESTRICT` |
| `target_type` | `pos_cancel_target` (enum) | `NN` (ITEM ou SALE) |
| `reason` | `VARCHAR(250)` | `NN` |
| `status` | `pos_cancel_status` (enum) | `NN` `def PENDING` |
| `requested_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `decided_at` / `executed_at` | `TIMESTAMP` | |
| `decision_observation` | `TEXT` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `(target_type='ITEM' AND sale_item_id NOT NULL) OR (target_type='SALE' AND sale_item_id IS NULL)`; `decided_at ≥ requested_at`; `executed_at IS NULL OR decided_at NOT NULL` |

---

*Próximo: [06 — Fidelidade e Promoções](06-fidelidade-promocoes.md)*
