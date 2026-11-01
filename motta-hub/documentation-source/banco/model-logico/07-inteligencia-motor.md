# 07 — Inteligência (Motor de Shelf Life)

Domínio do **cérebro** do Mottainai: o motor que **observa o estoque**, gera **alertas de risco**, **sugere ações**, e a camada de **IA** (previsão, recomendação, feedback e execução). Inclui a **telemetria do motor** (varreduras e sugestões) e as **regras configuráveis**.

```
alert ──< suggested_action ──1:1──> (promotion | transfer | donation | disposal)
ai_model ──< ai_prediction ──< ai_recommendation <──recom─ ai_feedback
ai_recommendation ──< ai_execution
engine_scan_log ──< engine_suggestion
system_rule (regras configuráveis: ENGINE / FINANCIAL / EXPIRATION / PRICE / GENERAL)
```

## `alert`

Aviso de risco de **vencimento, estoque crítico, ruptura, lentidão ou excesso** de uma loja.

| Coluna | Tipo | Restrições |
|---|---|---|
| `alert_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `title` | `VARCHAR(120)` | `NN` |
| `description` | `TEXT` | |
| `alert_type` | `alert_type` (enum) | `NN` (EXPIRATION / CRITICAL_STOCK / RUPTURE / SLOW_MOVING / OVERSTOCK) |
| `priority` | `priority_level` (enum) | `NN` `def MEDIUM` |
| `status` | `alert_status` (enum) | `NN` `def ACTIVE` |
| `generated_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `resolved_at` | `TIMESTAMP` | |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| ✅ `CHECK` | | `resolved_at IS NULL OR resolved_at ≥ generated_at` |

**Índices:** `idx_alert_active_store (store_id, priority) WHERE status='ACTIVE'`, `idx_alert_store_status_created (store_id, status, created_at) WHERE status='ACTIVE'`, `idx_alert_store_id`.

## `suggested_action`

Ação tática sugerida **a partir de um alerta** (promoção, transferência, doação, descarte, reabastecimento). Quando aprovada, gera o registro concreto (rascunho de promoção, transferência, etc.).

| Coluna | Tipo | Restrições |
|---|---|---|
| `suggested_action_id` 🔑 | `INTEGER` identity | `PK` |
| `alert_id` 🔗 | `INTEGER` | `NN` `FK → alert(alert_id) ON DELETE RESTRICT` |
| `action_type` | `suggested_action_type` (enum) | `NN` (PROMOTION / TRANSFER / DONATION / DISPOSAL / REORDER) |
| `description` | `TEXT` | |
| `priority` | `priority_level` (enum) | `NN` `def MEDIUM` |
| `status` | `suggested_action_status` (enum) | `NN` `def PENDING` |
| `generated_at` | `TIMESTAMP` | `NN` `def NOW()` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

> **Nó integrador:** `promotion.suggested_action_id`, `transfer.suggested_action_id`, `donation.suggested_action_id` e `disposal.suggested_action_id` apontam para esta tabela.

## Camada de IA

### `ai_model`

Modelo de IA cadastrado (previsão, recomendação, classificação, otimização).

| Coluna | Tipo | Restrições |
|---|---|---|
| `model_id` 🔑 | `INTEGER` identity | `PK` |
| `name` | `VARCHAR(100)` | `NN` |
| `version` | `VARCHAR(20)` | `NN` |
| `model_type` | `ai_model_type` (enum) | `NN` (FORECAST / RECOMMENDATION / CLASSIFICATION / OPTIMIZATION) |
| `description` | `TEXT` | |
| `parameters` | `JSONB` | |
| `accuracy` ✅ | `DECIMAL(5,2)` | |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| 🔎 `UQ` | | `(name, version)` |

### `ai_prediction`

Saída de previsão (demanda/quantidade) por produto e loja, com a **quantidade real** para comparação.

| Coluna | Tipo | Restrições |
|---|---|---|
| `prediction_id` 🔑 | `BIGSERIAL` | `PK` |
| `model_id` 🔗 | `INTEGER` | `NN` `FK → ai_model(model_id) ON DELETE RESTRICT` |
| `product_id` 🔗 | `INTEGER` | `FK → product(product_id) ON DELETE SET NULL` |
| `store_id` 🔗 | `INTEGER` | `FK → retail_store(store_id) ON DELETE SET NULL` |
| `predicted_date` | `DATE` | `NN` |
| `confidence` | `DECIMAL(5,2)` | |
| `predicted_quantity` | `DECIMAL(10,3)` | |
| `actual_quantity` | `DECIMAL(10,3)` | valor real para avaliação |
| `created_at` | `TIMESTAMP` | `def NOW()` |

### `ai_recommendation`

Recomendação de ação derivada de uma previsão, dirigida ao operador.

| Coluna | Tipo | Restrições |
|---|---|---|
| `recommendation_id` 🔑 | `BIGSERIAL` | `PK` |
| `prediction_id` 🔗 | `INTEGER` | `FK → ai_prediction(prediction_id) ON DELETE CASCADE` |
| `action_type` | `suggested_action_type` (enum) | `NN` |
| `priority` | `priority_level` (enum) | `NN` `def MEDIUM` |
| `reason` | `TEXT` | |
| `status` | `suggested_action_status` (enum) | `NN` `def PENDING` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |

### `ai_feedback`

Feedback do operador sobre uma recomendação (avaliação 1–5) — alimenta o aprendizado.

| Coluna | Tipo | Restrições |
|---|---|---|
| `feedback_id` 🔑 | `BIGSERIAL` | `PK` |
| `recommendation_id` 🔗 | `INTEGER` | `NN` `FK → ai_recommendation(recommendation_id) ON DELETE CASCADE` |
| `user_id` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `rating` ✅ | `INTEGER` | `NN` `CHECK 1..5` |
| `comment` | `TEXT` | |
| `created_at` | `TIMESTAMP` | `def NOW()` |

### `ai_execution`

Registro da execução de uma recomendação.

| Coluna | Tipo | Restrições |
|---|---|---|
| `execution_id` 🔑 | `BIGSERIAL` | `PK` |
| `recommendation_id` 🔗 | `INTEGER` | `NN` `FK → ai_recommendation(recommendation_id) ON DELETE CASCADE` |
| `executed_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `result` | `JSONB` | |
| `success` | `BOOLEAN` | `NN` `def TRUE` |

## Telemetria do motor

### `engine_scan_log`

Registro de cada **ciclo de varredura** do motor (SKUs escaneados, diagnósticos, assertividade).

| Coluna | Tipo | Restrições |
|---|---|---|
| `scan_id` 🔑 | `BIGSERIAL` | `PK` |
| `store_id` 🔗 | `INTEGER` | `FK → retail_store(store_id) ON DELETE CASCADE` |
| `scanned_at` | `TIMESTAMP` | `NN` `def NOW()` |
| `skus_scanned` ✅ | `INTEGER` | `NN` `def 0` `CHECK ≥ 0` |
| `diagnostics_count` ✅ | `INTEGER` | `NN` `def 0` `CHECK ≥ 0` |
| `assertiveness_rate` ✅ | `DECIMAL(5,2)` | `CHECK NULL OU 0..100` |
| `status` ✅ | `VARCHAR(20)` | `NN` `def COMPLETED` |

**Índice:** `idx_engine_scan_store_time (store_id, scanned_at)`.

### `engine_suggestion`

**Sugestão concreta do motor** (aceita/rejeitada/editada/executada pelo operador) durante uma varredura.

| Coluna | Tipo | Restrições |
|---|---|---|
| `suggestion_id` 🔑 | `BIGSERIAL` | `PK` |
| `scan_id` 🔗 | `BIGINT` | `FK → engine_scan_log(scan_id) ON DELETE SET NULL` |
| `store_id` 🔗 | `INTEGER` | `FK → retail_store(store_id) ON DELETE CASCADE` |
| `product_id` 🔗 | `INTEGER` | `FK → product(product_id) ON DELETE CASCADE` |
| `tactic` | `VARCHAR(50)` | `NN` |
| `suggested_action` | `VARCHAR(200)` | descrição da ação |
| `status` ✅ | `VARCHAR(20)` | `NN` `def PENDING` `CHECK IN ('PENDING','ACCEPTED','REJECTED','EDITED','EXECUTED')` |
| `proposal` | `JSONB` | detalhe da proposta |
| `decision_at` | `TIMESTAMP` | |
| `acted_by` 🔗 | `INTEGER` | `FK → app_user(user_id) ON DELETE SET NULL` |
| `created_at` | `TIMESTAMP` | `def NOW()` |

**Índices:** `idx_engine_suggestion_store_status (store_id, status)`, `idx_engine_suggestion_tactic (tactic)`.

## Regras configuráveis

### `system_rule`

Regras parametrizáveis que dirigem o motor e regras financeiras/validade/preço.

| Coluna | Tipo | Restrições |
|---|---|---|
| `rule_id` 🔑 | `INTEGER` identity | `PK` |
| `rule_category` ✅ | `VARCHAR(30)` | `NN` `CHECK IN ('ENGINE','FINANCIAL','EXPIRATION','PRICE','GENERAL')` |
| `rule_key` | `VARCHAR(60)` | `NN` |
| `rule_name` | `VARCHAR(120)` | |
| `rule_value` | `TEXT` | |
| `value_type` ✅ | `VARCHAR(20)` | `NN` `def TEXT` `CHECK IN ('TEXT','NUMBER','BOOLEAN','JSON')` |
| `description` | `TEXT` | |
| `active` | `BOOLEAN` | `NN` `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at` |
| 🔎 `UQ` | | `(rule_category, rule_key)` |

---

*Próximo: [08 — Logística e Sustentabilidade](08-logistica-sustentabilidade.md)*
