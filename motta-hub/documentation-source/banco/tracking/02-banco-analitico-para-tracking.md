# Banco analítico — referência para tracking

Esta é a referência de campos do banco analítico para o tracking centralizado.
Ela elimina a lacuna “sem colunas documentadas” do material anterior.

## Identificação e limites

| Item | Valor |
|---|---|
| Database físico | `MOTTANAI_ANALITICO` / `mottainai_analytics` conforme o ambiente |
| Schema principal | `mottainai_analytics` |
| Natureza | OLAP, modelo dimensional, leitura para BI e IA |
| Fonte | banco operacional físico |
| Frequência oficial | diária às `02:00`, fuso `America/Sao_Paulo` |
| Data de negócio | dia anterior ao horário agendado |
| Escrita | role de loader; dashboards usam role somente leitura |
| Relação com operacional | IDs correlacionados, sem FK entre databases |

O analítico não é réplica indiscriminada. Ele recebe dados de negócio
selecionados, minimiza identidade e exclui autenticação, sessões, envelopes
criptográficos, logs sensíveis e payloads operacionais.

## Dimensões

### `dim_date` — um dia do calendário

| Campo | Tipo | Obrigatório | Regra |
|---|---|---:|---|
| `date_key` | `DATE` | sim | PK |
| `year_number` | `SMALLINT` | sim | ano |
| `quarter_number` | `SMALLINT` | sim | 1 a 4 |
| `month_number` | `SMALLINT` | sim | 1 a 12 |
| `month_name` | `VARCHAR(12)` | sim | nome do mês |
| `week_number` | `SMALLINT` | sim | semana do ano |
| `day_number` | `SMALLINT` | sim | 1 a 31 |
| `day_of_week_number` | `SMALLINT` | sim | 1 a 7 |
| `day_of_week_name` | `VARCHAR(12)` | sim | nome do dia |
| `is_weekend` | `BOOLEAN` | sim | fim de semana |

### Dimensões de negócio

| Tabela | Grão | Campos físicos |
|---|---|---|
| `dim_company` | uma empresa | `company_id BIGINT PK`, `plan_id BIGINT`, `legal_name VARCHAR(255) NN`, `trade_name VARCHAR(255)`, `active BOOLEAN NN`, `source_updated_at TIMESTAMPTZ`, `loaded_at TIMESTAMPTZ NN`, `plan_name VARCHAR(150)` |
| `dim_store` | uma loja | `store_id BIGINT PK`, `company_id BIGINT NN`, `name VARCHAR(255) NN`, `city VARCHAR(120)`, `state_code CHAR(2)`, `latitude NUMERIC(10,7)`, `longitude NUMERIC(10,7)`, `active BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |
| `dim_category` | uma categoria | `category_id BIGINT PK`, `parent_category_id BIGINT`, `name VARCHAR(150) NN`, `active BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |
| `dim_product` | um produto | `product_id BIGINT PK`, `category_id`, `tax_profile_id`, `sku VARCHAR(100)`, `barcode VARCHAR(100)`, `name VARCHAR(255) NN`, `brand VARCHAR(120)`, `unit_of_measure VARCHAR(30)`, `avg_cost NUMERIC(15,4)`, `suggested_price NUMERIC(15,4)`, `active BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |
| `dim_supplier` | um fornecedor | `supplier_id BIGINT PK`, `company_id BIGINT NN`, `name VARCHAR(255) NN`, `city VARCHAR(120)`, `state_code CHAR(2)`, `active BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |
| `dim_employee` | funcionário sem identidade | `employee_id BIGINT PK`, `store_id BIGINT`, `role_id BIGINT`, `role_name VARCHAR(100)`, `active BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |
| `dim_customer` | cliente anonimizado | `customer_id BIGINT PK`, `anonymous_key UUID NN UQ`, `birth_year SMALLINT`, `active BOOLEAN NN`, `marketing_consent BOOLEAN NN`, `source_updated_at`, `loaded_at NN` |

`dim_employee` nunca recebe nome, CPF, e-mail ou telefone. `dim_customer` nunca
recebe identidade ou contato.

## Fatos

| Tabela | Grão | Chave e campos |
|---|---|---|
| `fact_sales` | uma venda por data | `sale_id BIGINT`, `sale_date DATE`, `sale_timestamp TIMESTAMPTZ`, `company_id/store_id BIGINT`, `employee_id/customer_id BIGINT`, `item_count INTEGER`, `gross_amount/discount_amount/net_amount NUMERIC(15,2)`, `status VARCHAR(30)`, `loaded_at TIMESTAMPTZ`; PK `(sale_id, sale_date)` |
| `fact_sale_item` | um item por venda e data | `sale_item_id/sale_id/store_id/product_id/batch_id BIGINT`, `sale_date DATE`, `quantity NUMERIC(15,3)`, `unit_price NUMERIC(15,4)`, `discount_amount/subtotal NUMERIC(15,2)`, `loaded_at TIMESTAMPTZ`; PK `(sale_item_id, sale_date)` |
| `fact_sale_payment` | um pagamento | `payment_id/sale_id/store_id BIGINT`, `sale_date DATE`, `payment_method VARCHAR(40)`, `amount NUMERIC(15,2)`, `installments SMALLINT`, `loaded_at TIMESTAMPTZ`; PK `payment_id` |
| `fact_inventory_movement` | uma movimentação por data | IDs `BIGINT`, `movement_date DATE`, `movement_timestamp TIMESTAMPTZ`, `movement_type VARCHAR(40)`, `quantity NUMERIC(15,3)`, `unit_cost NUMERIC(15,4)`, `loaded_at TIMESTAMPTZ`; PK `(movement_id, movement_date)` |
| `fact_inventory_snapshot` | posição diária por loja, produto, lote e tipo | `snapshot_date DATE`, IDs `BIGINT`, `inventory_type VARCHAR(30)`, `quantity/reserved_quantity/minimum_quantity NUMERIC(15,3)`, `average_cost NUMERIC(15,4)`, `expiration_date DATE`, `loaded_at TIMESTAMPTZ`; PK composta |
| `fact_purchase_order` | um pedido por data | IDs `BIGINT`, `order_date DATE`, `status VARCHAR(30)`, `item_count INTEGER`, `total_amount NUMERIC(15,2)`, `loaded_at TIMESTAMPTZ`; PK `(purchase_order_id, order_date)` |
| `fact_receiving` | um recebimento | IDs `BIGINT`, `receiving_date DATE`, `status VARCHAR(30)`, `item_count INTEGER`, `loaded_at TIMESTAMPTZ`; PK `receiving_id` |
| `fact_promotion_result` | promoção, dia, loja e produto | IDs `BIGINT`, `result_date DATE`, `units_sold NUMERIC(15,3)`, valores `NUMERIC(15,2)`, `loaded_at TIMESTAMPTZ`; PK composta |
| `fact_loss_destination` | uma destinação de perda | IDs `BIGINT`, `loss_date DATE`, `destination_type VARCHAR(40)`, `quantity NUMERIC(15,3)`, `estimated_value NUMERIC(15,2)`, `loaded_at TIMESTAMPTZ`; PK `loss_id` |
| `fact_transfer` | uma transferência | IDs `BIGINT`, `transfer_date DATE`, `status VARCHAR(30)`, `item_count INTEGER`, `total_cost NUMERIC(15,2)`, `loaded_at TIMESTAMPTZ`; PK `transfer_id` |
| `fact_replenishment` | reposição por produto | IDs `BIGINT`, `replenishment_date DATE`, quantidades `NUMERIC(15,3)`, `status VARCHAR(30)`, `loaded_at TIMESTAMPTZ`; PK `replenishment_id` |
| `fact_loyalty` | um evento de pontos | IDs `BIGINT`, `event_date DATE`, `event_type VARCHAR(30)`, `points_delta/balance_after INTEGER`, `loaded_at TIMESTAMPTZ`; PK `loyalty_event_id` |
| `fact_store_daily` | uma loja por dia | `snapshot_date DATE`, `company_id/store_id BIGINT`, contagens `INTEGER`, `captured_at TIMESTAMPTZ`; PK `(snapshot_date, store_id)` |
| `fact_alert_snapshot` | um alerta por dia | `snapshot_date DATE`, `alert_id/store_id BIGINT`, `status VARCHAR(30)`; PK `(snapshot_date, alert_id)` |

Os quatro fatos de vendas/estoque de maior volume são particionados mensalmente
e possuem partição default.

## IA e recomendações

| Tabela | Finalidade | Campos principais |
|---|---|---|
| `ai_model` | catálogo/versionamento | ID, nome, tipo, versão, parâmetros, métricas, estado e datas |
| `ai_prediction` | inferência | modelo, escopo, tipo, valor, confiança, horizonte, features e explicação |
| `ai_recommendation` | recomendação acionável | predição, escopo, ação, prioridade, status, justificativa, impacto e correlação operacional |
| `ai_feedback` | decisão humana | recomendação, usuário, decisão, motivo, resultado e data |
| `ai_execution` | execução de modelo | modelo, início/fim, status, linhas, erro e metadados |
| `engine_scan_log` | varredura do motor | escopo, tipo, datas, status, contagens, erro e metadados |
| `engine_suggestion` | sugestão produzida | scan, recomendação, escopo, ação, prioridade, status e correlação operacional |
| `kpi_cache` | KPI por escopo/data | PK composta, valor, payload, cálculo e expiração |

## Ingestão, reconciliação e publicação

| Tabela | Finalidade | Campos principais |
|---|---|---|
| `etl_pipeline_config` | configuração do pipeline | nome, fonte, fuso, horário, retenção e estado |
| `etl_source_contract` | contrato por origem | ordem, modo, watermark, destino, política e obrigatoriedade |
| `etl_daily_batch` | execução diária | UUID, data, agendamento, cutoff, estado, contagens, marcos e erro |
| `stg_operational_row` | staging idempotente | batch, tabela/chave, empresa, loja, payload, datas e SHA-256 |
| `etl_rejected_row` | linha rejeitada | batch, origem, hash, motivo e data |
| `etl_reconciliation` | conferência | esperado, staged, igualdade e data |
| `etl_table_checkpoint` | watermark por tabela | batch/data/chave/atualização, linhas e publicação |
| `ingestion_event` | ingestão de evento | UUID, origem, tipo, agregado, escopo, payload, datas e estado |
| `etl_checkpoint` | checkpoint genérico | último evento/ID/data e metadados |
| `etl_dead_letter` | falhas | evento, pipeline, payload, erro, tentativas e resolução |
| `job_log` | execução técnica | job, estado, datas, contagens, erro, metadados e batch |
| `query_performance` | desempenho | consulta, duração, linhas, data e metadados |

Estados do batch: `EXTRACTING`, `STAGED`, `TRANSFORMING`, `VALIDATED`,
`PUBLISHED` e `FAILED`. Views publicadas só consomem batch `PUBLISHED`.

## Views para BI

| View | Uso |
|---|---|
| `vw_published_batch` | último lote publicado |
| `vw_sales_daily_kpis` | KPIs diários de venda |
| `vw_top_selling_products` | ranking de produtos |
| `vw_inventory_snapshot_current` | estoque mais recente |
| `vw_stockout_analysis`, `vw_critical_stock` | ruptura e estoque crítico |
| `vw_monthly_summary` | vendas mensais por loja |
| `vw_product_risk_ranking` | risco de ruptura e vencimento |
| `mv_dashboard_metrics` | métricas materializadas por loja |
| `vw_company_kpis` | indicadores por empresa |
| `vw_employee_distribution` | distribuição por papel, sem PII |
| `vw_store_daily_kpis` | série diária por loja |
| `vw_ai_performance`, `vw_engine_suggestion_metrics` | desempenho da IA |
| `vw_executive_dashboard` | visão executiva |
| `vw_customer_loyalty_analysis` | fidelidade anônima |
| `vw_etl_daily_batch_health` | saúde da carga diária |

## Mapeamento operacional → analítico

| Origem | Destino | Política |
|---|---|---|
| empresa e plano | `dim_company` | negócio |
| loja e endereço | `dim_store` | localização minimizada |
| funcionário e papel | `dim_employee` | sem identidade |
| categoria, produto e tributo | dimensões correspondentes | negócio |
| fornecedor e endereço | `dim_supplier` | sem contatos |
| pedidos e recebimentos | fatos correspondentes | negócio |
| estoque, lote e movimentos | fatos de estoque | negócio |
| venda, item e pagamento | fatos de venda | cliente minimizado |
| cliente, consentimento e fidelidade | `dim_customer`, `fact_loyalty` | anônimo |
| promoções, perdas, transferências e reposição | fatos correspondentes | negócio |
| alertas e ações | snapshot e motor | negócio |

## Objetos proibidos na carga analítica

- `employee_private_data` e `customer_private_data`;
- `app_user`, `customer_auth`, `staff_session` e `password_reset_token`;
- `audit_log`, `system_log`, `error_log` e `integration_log`;
- `event_queue` e `legacy_sync_record`.

Também são proibidos em payload: CPF, CNPJ, e-mail, telefone, nome, senha,
token, ciphertext, nonce, Firebase UID, external auth UID e refresh-token hash.

## Critério de aceite

O tracking deve conter grão e campos das dimensões e fatos, marcar views como
objetos derivados, identificar medidas e chaves, manter o batch das 02:00 e não
reproduzir identidade, credencial ou envelope criptográfico.

