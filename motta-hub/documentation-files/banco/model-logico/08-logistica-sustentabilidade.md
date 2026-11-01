# 08 — Logística e Sustentabilidade

Domínio da **redistribuição e redução de perdas**: transferências entre lojas, doações a instituições e avarias/descarte. Todos os registros podem ter origem em uma **ação sugerida** (`suggested_action_id`) e carregam **trigger de auditoria** (`audit_log`).

```
store ──< transfer ──> store (transferência entre lojas; suggested_action de origem)
transfer ──< transfer_item ──> batch
donation ──< donation_item ──> batch
disposal ──< disposal_item ──> batch
```

## `transfer`

Movimentação de mercadoria **entre lojas** (ex.: produto próximo do vencimento para filial de maior giro).

| Coluna | Tipo | Restrições |
|---|---|---|
| `transfer_id` 🔑 | `INTEGER` identity | `PK` |
| `suggested_action_id` 🔗 | `INTEGER` | `FK → suggested_action(suggested_action_id) ON DELETE SET NULL` |
| `source_store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `destination_store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `request_date` | `TIMESTAMP` | `NN` `def NOW()` |
| `completion_date` | `TIMESTAMP` | |
| `status` | `transfer_status` (enum) | `NN` `def REQUESTED` |
| `observation` | `TEXT` | |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `source_store_id ≠ destination_store_id`; `completion_date IS NULL OR completion_date ≥ request_date` |

**Trigger:** `trg_audit_transfer` — grava `INSERT/UPDATE/DELETE` em `audit_log` (arg: `transfer_id`).

## `transfer_item`

Item da transferência (lote e quantidade).

| Coluna | Tipo | Restrições |
|---|---|---|
| `transfer_item_id` 🔑 | `INTEGER` identity | `PK` |
| `transfer_id` 🔗 | `INTEGER` | `NN` `FK → transfer(transfer_id) ON DELETE CASCADE` |
| `batch_id` 🔗 | `INTEGER` | `NN` `FK → batch(batch_id) ON DELETE RESTRICT` |
| `transferred_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `donation`

Doação de alimentos a instituições — **pilar de impacto socioambiental**.

| Coluna | Tipo | Restrições |
|---|---|---|
| `donation_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `suggested_action_id` 🔗 | `INTEGER` | `FK → suggested_action(suggested_action_id) ON DELETE SET NULL` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `institution` | `VARCHAR(150)` | `NN` |
| `donation_date` | `TIMESTAMP` | `NN` `def NOW()` |
| `status` | `donation_status` (enum) | `NN` `def REGISTERED` |
| `observation` | `TEXT` | |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

**Trigger:** `trg_audit_donation` — grava em `audit_log` (arg: `donation_id`).

## `donation_item`

Item doado (lote e quantidade).

| Coluna | Tipo | Restrições |
|---|---|---|
| `donation_item_id` 🔑 | `INTEGER` identity | `PK` |
| `donation_id` 🔗 | `INTEGER` | `NN` `FK → donation(donation_id) ON DELETE CASCADE` |
| `batch_id` 🔗 | `INTEGER` | `NN` `FK → batch(batch_id) ON DELETE RESTRICT` |
| `donated_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

## `disposal`

Avarias e descarte interno (produto impróprio para venda/doação).

| Coluna | Tipo | Restrições |
|---|---|---|
| `disposal_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `suggested_action_id` 🔗 | `INTEGER` | `FK → suggested_action(suggested_action_id) ON DELETE SET NULL` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `reason` | `VARCHAR(100)` | `NN` |
| `disposal_date` | `TIMESTAMP` | `NN` `def NOW()` |
| `observation` | `TEXT` | |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

**Trigger:** `trg_audit_disposal` — grava em `audit_log` (arg: `disposal_id`).

## `disposal_item`

Item descartado (lote e quantidade).

| Coluna | Tipo | Restrições |
|---|---|---|
| `disposal_item_id` 🔑 | `INTEGER` identity | `PK` |
| `disposal_id` 🔗 | `INTEGER` | `NN` `FK → disposal(disposal_id) ON DELETE CASCADE` |
| `batch_id` 🔗 | `INTEGER` | `NN` `FK → batch(batch_id) ON DELETE RESTRICT` |
| `disposed_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

---

*Próximo: [09 — Auditoria e Observabilidade](09-auditoria-observabilidade.md)*
