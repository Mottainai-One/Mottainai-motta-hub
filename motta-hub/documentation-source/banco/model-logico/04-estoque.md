# 04 — Estoque

Domínio do **inventário físico**: lotes rastreáveis, saldo por loja/`inventory_type`, movimentação e reposição (pré-lista e execução). O estoque é a base do **FEFO** e do motor de inteligência.

```
product ──< batch ──< inventory (por loja + tipo) ──< inventory_movement
store ──┘   (receiving_item de origem)
store ──< replenishment_pre_list ──< replenishment_pre_list_item ──> product
       ──< replenishment_execution ──< replenishment_execution_item ──> batch
```

## `batch`

Lote rastreável de um produto, com **data de validade** — base do FEFO e do cálculo de custo médio.

| Coluna | Tipo | Restrições |
|---|---|---|
| `batch_id` 🔑 | `INTEGER` identity | `PK` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(product_id) ON DELETE RESTRICT` |
| `receiving_item_id` 🔗 | `INTEGER` | `FK → receiving_item(receiving_item_id) ON DELETE SET NULL` |
| `batch_code` 🔎 | `VARCHAR(60)` | `NN` (gerado pela sequência `batch_code_seq` quando a origem é o recebimento) |
| `manufacture_date` | `DATE` | |
| `expiration_date` ✅ | `DATE` | `NN` |
| `initial_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `unit_cost` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `active` | `BOOLEAN` | `def TRUE` |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |
| ✅ `CHECK` | | `manufacture_date IS NULL OR manufacture_date ≤ expiration_date` |

**Triggers:**
- `trg_create_batch` (_AFTER INSERT on `receiving_item`_) — cria o lote a partir do item recebido.
- `trg_batch_update_cost` (_AFTER INSERT_) — recalcula `avg_cost`/`suggested_price` do produto e grava `product_price_history` (RF16).

**Índices:** `idx_batch_product_expiration (product_id, expiration_date)` (apoia FEFO), `idx_batch_product_id`, `idx_batch_receiving_item_id`.

## `inventory`

Saldo atual de um **lote** em uma **loja**, discriminado por **tipo** (normal, consignado, quarentena de avarias).

| Coluna | Tipo | Restrições |
|---|---|---|
| `inventory_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `batch_id` 🔗 | `INTEGER` | `NN` `FK → batch(batch_id) ON DELETE RESTRICT` |
| `inventory_type` | `inventory_type` (enum) | `NN` `def NORMAL` |
| `current_quantity` ✅ | `DECIMAL(10,3)` | `NN` `def 0` `CHECK ≥ 0` |
| `minimum_quantity` ✅ | `DECIMAL(10,3)` | `NN` `def 0` `CHECK ≥ 0` |
| `maximum_quantity` ✅ | `DECIMAL(10,3)` | `CHECK NULL OU ≥ minimum_quantity` |
| `location` | `VARCHAR(80)` | posição física na loja |
| `version` | `INTEGER` | `def 1` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |
| 🔎 `UQ` | | `(store_id, batch_id, inventory_type)` |

**Observações:** sujeita a **RLS** (`inventory_policy` → `store_id IN (lojas da empresa)`).

**Índices:** `idx_inventory_positive (store_id, batch_id) WHERE current_quantity>0 AND deleted_at IS NULL`, `idx_inventory_store_product (store_id, batch_id)`, `idx_inventory_batch_id`.

## `inventory_movement`

Todo evento de entrada/saída/ajuste do estoque (granularidade fina; histórico de auditoria). **Tabela particionada por `movement_date`** (PK composta).

| Coluna | Tipo | Restrições |
|---|---|---|
| `movement_id` 🔑 | `INTEGER` identity | parte da `PK (movement_id, movement_date)` |
| `inventory_id` 🔗 | `INTEGER` | `NN` `FK → inventory(inventory_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `FK → employee(employee_id) ON DELETE SET NULL` |
| `movement_date` 🔑 | `TIMESTAMP` | parte da PK · coluna de partição · `def NOW()` |
| `movement_type` | `movement_type` (enum) | `NN` (IN / OUT / ADJUSTMENT / TRANSFER / DONATION / DISPOSAL) |
| `moved_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK ≠ 0` (sinal conforme o sentido) |
| `previous_balance` ✅ | `DECIMAL(10,3)` | `NN` `CHECK ≥ 0` |
| `current_balance` ✅ | `DECIMAL(10,3)` | `NN` `CHECK ≥ 0` |
| `observation` | `TEXT` | |
| `store_id` | `INTEGER` | denormalização para consulta |
| `created_at` | `TIMESTAMP` | `def NOW()` |
| ✅ `CHECK` | | `ck_movement_direction`: OUT/DISPOSAL → `moved_quantity < 0`; IN → `> 0`; ADJUSTMENT/TRANSFER/DONATION → `≠ 0` |

**Observações:** particionada; gerenciamento automático de partições via procedures (`sp_create_future_partitions`/`sp_drop_old_partitions`). `idx_inventory_movement_inventory_id`.

## `inventory_count_item`

Linha de uma contagem física, preservada para reconciliação e auditoria.

| Coluna | Tipo | Restrições |
|---|---|---|
| `inventory_count_item_id` 🔑 | `BIGSERIAL` | `PK` |
| `inventory_count_id` 🔗 | `BIGINT` | `NN` `FK → inventory_count` |
| `inventory_id` 🔗 | `INTEGER` | `NN` `FK → inventory` |
| `system_quantity` / `counted_quantity` | `DECIMAL(12,3)` | `NN` |
| `difference` | `DECIMAL(12,3)` | valor gerado |
| `observation` | `TEXT` | |
| `created_at` | `TIMESTAMPTZ` | `NN` `def CURRENT_TIMESTAMP` |
| `deleted_at` | `TIMESTAMPTZ` | exclusão lógica esperada pela API |

## Reposição (abastecimento)

### `replenishment_pre_list`

Pré-lista de abastecimento para uma loja (itens a retirar da câmara-fria).

| Coluna | Tipo | Restrições |
|---|---|---|
| `pre_list_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `FK → employee(employee_id) ON DELETE SET NULL` |
| `generated_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `status` | `pre_list_status` (enum) | `NN` `def GENERATED` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

### `replenishment_pre_list_item`

Item da pré-lista (produto, quantidade sugerida e prioridade).

| Coluna | Tipo | Restrições |
|---|---|---|
| `pre_list_item_id` 🔑 | `INTEGER` identity | `PK` |
| `pre_list_id` 🔗 | `INTEGER` | `NN` `FK → replenishment_pre_list(pre_list_id) ON DELETE CASCADE` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(product_id) ON DELETE RESTRICT` |
| `suggested_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `priority` | `priority_level` (enum) | `NN` `def MEDIUM` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

### `replenishment_execution`

Execução da reposição (retirada física), com avaliação do processo.

| Coluna | Tipo | Restrições |
|---|---|---|
| `execution_id` 🔑 | `INTEGER` identity | `PK` |
| `pre_list_id` 🔗 | `INTEGER` | `NN` `FK → replenishment_pre_list(pre_list_id) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `start_date` | `TIMESTAMP` | `NN` `def NOW()` |
| `end_date` | `TIMESTAMP` | |
| `rating` ✅ | `INTEGER` | `CHECK 1..5` |
| `comment` | `TEXT` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `end_date IS NULL OR end_date ≥ start_date` |

### `replenishment_execution_item`

Item executado (lote e quantidade reposta).

| Coluna | Tipo | Restrições |
|---|---|---|
| `execution_item_id` 🔑 | `INTEGER` identity | `PK` |
| `execution_id` 🔗 | `INTEGER` | `NN` `FK → replenishment_execution(execution_id) ON DELETE CASCADE` |
| `batch_id` 🔗 | `INTEGER` | `NN` `FK → batch(batch_id) ON DELETE RESTRICT` |
| `replenished_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

---

*Próximo: [05 — Vendas e PDV](05-vendas-pdv.md)*
