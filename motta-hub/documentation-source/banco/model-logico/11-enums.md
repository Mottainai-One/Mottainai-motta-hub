# 11 — Enums

Os estados de negócio são modelados de duas formas no banco:

1. **Tipos `enum` nativos do PostgreSQL** (listados abaixo).
2. **Colunas `VARCHAR` com `CHECK` inline** para estados mais simples ou específicos de uma superfície (PDV, motor, etc.), documentados nas respectivas tabelas.

## Tipos ENUM (schema `mottainai`)

| Tipo | Valores | Usado em |
|---|---|---|
| `migration_type` | `SQL`, `JAVA`, `GROOVY`, `SCRIPT` | `schema_version.type` |
| `purchase_order_status` | `PENDING`, `APPROVED`, `CANCELED` | `purchase_order.status` |
| `receiving_status` | `PENDING`, `CONFIRMED`, `DIVERGENT` | `receiving.status` |
| `sale_status` | `COMPLETED`, `CANCELED`, `RETURNED` | `sales_transaction.status` |
| `sale_item_status` | `SOLD`, `CANCELED`, `RETURNED` | `sale_item.status` |
| `pos_cancel_status` | `PENDING`, `APPROVED`, `REJECTED`, `EXECUTED`, `CANCELED` | `pos_cancel_request.status` |
| `pos_cancel_target` | `ITEM`, `SALE` | `pos_cancel_request.target_type` |
| `promotion_status` | `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `EXPIRED`, `CANCELLED` | `promotion.status` |
| `movement_type` | `IN`, `OUT`, `ADJUSTMENT`, `TRANSFER`, `DONATION`, `DISPOSAL` | `inventory_movement.movement_type` |
| `inventory_type` | `NORMAL`, `CONSIGNED`, `QUARANTINE` | `inventory.inventory_type` |
| `inventory_status` | `IN_PROGRESS`, `COMPLETED`, `CANCELED` | *(definido, sem uso em coluna)* |
| `priority_level` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | `alert.priority`, `suggested_action.priority`, `ai_recommendation.priority`, `replenishment_pre_list_item.priority` |
| `payment_method` | `CASH`, `CARD`, `PIX`, `BOLETO` | `sale_payment.payment_method` |
| `alert_status` | `ACTIVE`, `ANALYZING`, `RESOLVED`, `IGNORED` | `alert.status` |
| `alert_type` | `EXPIRATION`, `CRITICAL_STOCK`, `RUPTURE`, `SLOW_MOVING`, `OVERSTOCK` | `alert.alert_type` |
| `suggested_action_status` | `PENDING`, `APPROVED`, `REJECTED`, `EXECUTED` | `suggested_action.status`, `ai_recommendation.status` |
| `suggested_action_type` | `PROMOTION`, `TRANSFER`, `DONATION`, `DISPOSAL`, `REORDER`, `PURCHASE_ORDER` | `suggested_action.action_type`, `ai_recommendation.action_type` |
| `pre_list_status` | `GENERATED`, `IN_PROGRESS`, `COMPLETED`, `CANCELED` | `replenishment_pre_list.status` |
| `transfer_status` | `REQUESTED`, `IN_TRANSIT`, `COMPLETED`, `CANCELED` | `transfer.status` |
| `donation_status` | `REGISTERED`, `COMPLETED`, `CANCELED` | `donation.status` |
| `audit_operation` | `INSERT`, `UPDATE`, `DELETE` | `audit_log.operation` |
| `ai_model_type` | `FORECAST`, `RECOMMENDATION`, `CLASSIFICATION`, `OPTIMIZATION` | `ai_model.model_type` |
| `event_status` | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELED` | `event_queue.status` |
| `log_level` | `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL` | `system_log.log_level` |

## Estados por `VARCHAR` + `CHECK` (documentados nas tabelas)

| Tabela · coluna | Valores permitidos |
|---|---|
| `pos_shift.status` | `OPEN`, `CLOSED`, `CANCELED` |
| `pos_cash_movement.movement_type` | `SANGRIA`, `SUPRIMENTO` |
| `fiscal_document.document_type` | `NFE`, `NFCE`, `SAT` |
| `fiscal_document.status` | `PENDING`, `AUTHORIZED`, `CANCELED`, `REJECTED` |
| `promotion.promotion_type` | `DISCOUNT_PERCENT`, `DISCOUNT_FIXED`, `SPECIAL_PRICE` |
| `loyalty_transaction.transaction_type` | `EARN`, `REDEEM`, `ADJUSTMENT`, `EXPIRE` |
| `loyalty_redemption.status` | `PENDING`, `CONFIRMED`, `CANCELED` |
| `engine_suggestion.status` | `PENDING`, `ACCEPTED`, `REJECTED`, `EDITED`, `EXECUTED` |
| `system_rule.rule_category` | `ENGINE`, `FINANCIAL`, `EXPIRATION`, `PRICE`, `GENERAL` |
| `system_rule.value_type` | `TEXT`, `NUMBER`, `BOOLEAN`, `JSON` |

---

*Fim do guia do modelo lógico. Voltar ao [índice](README.md).*
