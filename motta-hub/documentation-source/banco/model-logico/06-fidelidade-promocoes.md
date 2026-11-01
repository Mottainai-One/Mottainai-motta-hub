# 06 — Fidelidade e Promoções

Domínio de **engajamento do cliente**: acúmulo/resgate de pontos, recompensas, geocercas de proximidade e promoções.

```
customer ── 1:1 ── loyalty_account ──< loyalty_transaction
loyalty_account ──< loyalty_redemption ──> loyalty_reward
customer ──< customer_geofence ──> retail_store
promotion ──< promotion_item ──> product
promotion.suggested_action_id ──> suggested_action (origem do motor)
```

## `customer_geofence`

Configuração de proximidade **cliente ↔ loja** para alertas contextuais (raio em metros).

| Coluna | Tipo | Restrições |
|---|---|---|
| `geofence_id` 🔑 | `INTEGER` identity | `PK` |
| `customer_id` 🔗 | `INTEGER` | `NN` `FK → customer(customer_id) ON DELETE CASCADE` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE CASCADE` |
| `radius_meters` ✅ | `INTEGER` | `NN` `def 1000` `CHECK 50..10000` |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| 🔎 `UQ` | | `(customer_id, store_id)` |

**Índice:** `idx_customer_geofence_store (store_id) WHERE active`.

## `loyalty_account`

Conta de pontos do cliente (relação 1:1).

| Coluna | Tipo | Restrições |
|---|---|---|
| `loyalty_account_id` 🔑 | `INTEGER` identity | `PK` |
| `customer_id` 🔗 | `INTEGER` | `NN` `UQ` `FK → customer(customer_id) ON DELETE CASCADE` |
| `points_balance` ✅ | `INTEGER` | `NN` `def 0` `CHECK ≥ 0` |
| `joined_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| `updated_at` | `TIMESTAMP` | `def NOW()` |

## `loyalty_transaction`

Registro de ganho/resgate/ajuste/expiração de pontos (uma linha por evento).

| Coluna | Tipo | Restrições |
|---|---|---|
| `loyalty_transaction_id` 🔑 | `INTEGER` identity | `PK` |
| `loyalty_account_id` 🔗 | `INTEGER` | `NN` `FK → loyalty_account(loyalty_account_id) ON DELETE CASCADE` |
| `sale_id` 🔗 | `INTEGER` | `FK (sale_id, sale_date) → sales_transaction … ON DELETE SET NULL` |
| `sale_date` 🔗 | `TIMESTAMP` | (parte da FK composta) |
| `transaction_type` ✅ | `VARCHAR(20)` | `NN` `CHECK IN ('EARN','REDEEM','ADJUSTMENT','EXPIRE')` |
| `points` ✅ | `INTEGER` | `NN` `CHECK ≠ 0` |
| `description` | `VARCHAR(255)` | `NN` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

**Índice:** `idx_loyalty_transaction_account`.

## `loyalty_reward`

Prêmio resgatável por pontos.

| Coluna | Tipo | Restrições |
|---|---|---|
| `reward_id` 🔑 | `INTEGER` identity | `PK` |
| `name` | `VARCHAR(120)` | `NN` |
| `description` | `TEXT` | |
| `points_cost` ✅ | `INTEGER` | `NN` `CHECK > 0` |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| `valid_from` / `valid_until` | `TIMESTAMP` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from` |

## `loyalty_redemption`

Troca de pontos por uma recompensa.

| Coluna | Tipo | Restrições |
|---|---|---|
| `redemption_id` 🔑 | `INTEGER` identity | `PK` |
| `loyalty_account_id` 🔗 | `INTEGER` | `NN` `FK → loyalty_account(loyalty_account_id) ON DELETE RESTRICT` |
| `reward_id` 🔗 | `INTEGER` | `NN` `FK → loyalty_reward(reward_id) ON DELETE RESTRICT` |
| `points_spent` ✅ | `INTEGER` | `NN` `CHECK > 0` |
| `redeemed_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `status` ✅ | `VARCHAR(20)` | `NN` `def CONFIRMED` `CHECK IN ('PENDING','CONFIRMED','CANCELED')` |
| 🔎 `UQ` | | `(loyalty_account_id, reward_id, redeemed_at)` |

## `promotion`

Oferta promocional. Pode ser criada **manualmente** ou **sugerida pelo motor** (via `suggested_action_id`), com **fluxo de aprovação**.

| Coluna | Tipo | Restrições |
|---|---|---|
| `promotion_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `suggested_action_id` 🔗 | `INTEGER` | `FK → suggested_action(suggested_action_id) ON DELETE SET NULL` |
| `name` | `VARCHAR(150)` | `NN` |
| `description` | `TEXT` | |
| `promotion_type` ✅ | `VARCHAR(20)` | `NN` `CHECK IN ('DISCOUNT_PERCENT','DISCOUNT_FIXED','SPECIAL_PRICE')` |
| `starts_at` | `TIMESTAMP` | `NN` |
| `ends_at` | `TIMESTAMP` | `NN` |
| `status` | `promotion_status` (enum) | `NN` `def PENDING_APPROVAL` |
| `active` | `BOOLEAN` | `NN` `def FALSE` |
| `created_by` 🔗 | `INTEGER` | `FK → employee(employee_id) ON DELETE SET NULL` |
| `approved_by` 🔗 | `INTEGER` | `FK → employee(employee_id) ON DELETE SET NULL` |
| `approved_at` | `TIMESTAMP` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |
| ✅ `CHECK` | | `ends_at > starts_at` |

**Índice:** `idx_promotion_store_active (store_id, starts_at, ends_at) WHERE active`.

## `promotion_item`

Produto participante de uma promoção, com preços e **desconto percentual calculado** (gerado).

| Coluna | Tipo | Restrições |
|---|---|---|
| `promotion_item_id` 🔑 | `INTEGER` identity | `PK` |
| `promotion_id` 🔗 | `INTEGER` | `NN` `FK → promotion(promotion_id) ON DELETE CASCADE` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(product_id) ON DELETE RESTRICT` |
| `original_price` ✅ | `DECIMAL(12,2)` | `NN` `CHECK ≥ 0` |
| `promotional_price` ✅ | `DECIMAL(12,2)` | `NN` `CHECK ≥ 0` |
| `discount_percent` | `DECIMAL(7,4)` | **gerado** — `CASE WHEN original_price>0 THEN ((original_price-promotional_price)/original_price)*100 ELSE 0 END STORED` |
| `quantity_available` ✅ | `DECIMAL(12,3)` | `CHECK NULL OU ≥ 0` |
| `created_at` | `TIMESTAMP` | `def NOW()` |
| `deleted_at` | `TIMESTAMP` | exclusão lógica usada pelas APIs e views |
| 🔎 `UQ` | | `(promotion_id, product_id)` |
| ✅ `CHECK` | | `promotional_price ≤ original_price` |

---

*Próximo: [07 — Inteligência (Motor)](07-inteligencia-motor.md)*
