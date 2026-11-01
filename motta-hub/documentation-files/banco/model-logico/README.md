# Modelo Lógico — Mottainai

> **Banco Operacional** · PostgreSQL 15+ · versão 2026-10-02
> Detalhamento físico-lógico de tabelas, colunas, chaves, restrições, índices, triggers, RLS e integração com o banco analítico separado.

O **modelo lógico** descreve **como** o domínio conceitual foi materializado no banco. Ele detalha cada tabela, seus **atributos**, **tipos**, **chaves primárias e estrangeiras**, **restrições** (`CHECK`/`UNIQUE`), **índices**, **triggers** e **procedures**, além das regras e convenções adotadas. Serve de referência única para quem implementa, integra ou mantém o banco operacional.

> A camada de *conceitos de negócio* está no **[Modelo Conceitual](../modelo-conceitual/README.md)**. Este documento foca no *detalhamento físico*.

## Organização deste guia

| Documento | Conteúdo |
|---|---|
| [`README.md`](README.md) | Visão geral, navegação e leitura das tabelas (este arquivo) |
| [`01-schemas-e-convencoes.md`](01-schemas-e-convencoes.md) | Schemas, convenções adotadas e regras de projeto |
| [`02-cadastro-e-empresa.md`](02-cadastro-e-empresa.md) | Plano, Empresa, Loja, Funcionário, Usuário, Papel, Endereço |
| [`03-produto-e-compras.md`](03-produto-e-compras.md) | Produto, Categoria, Perfil Fiscal, Fornecedor, Pedido, Recebimento |
| [`04-estoque.md`](04-estoque.md) | Lote, Estoque, Movimentação, Reposição |
| [`05-vendas-pdv.md`](05-vendas-pdv.md) | Cliente, Terminal, Turno, Venda, Item, Pagamento, Documento Fiscal |
| [`06-fidelidade-promocoes.md`](06-fidelidade-promocoes.md) | Fidelidade, Geocerca, Promoção |
| [`07-inteligencia-motor.md`](07-inteligencia-motor.md) | Alerta, Ação Sugerida, IA, Varreduras/Telemetria do motor, Regras |
| [`08-logistica-sustentabilidade.md`](08-logistica-sustentabilidade.md) | Transferência, Doação, Avarias/Descarte |
| [`09-auditoria-observabilidade.md`](09-auditoria-observabilidade.md) | Auditoria, Logs, Eventos, Jobs, KPI, Históricos |
| [`10-camada-analitica.md`](10-camada-analitica.md) | Banco físico `mottainai_analytics` — modelo estrela, ingestão e indicadores |
| [`11-enums.md`](11-enums.md) | Todos os tipos enum e seus valores |
| [Segurança](../seguranca/01-arquitetura-de-seguranca.md) | Role da API, sessões, contexto transacional, RLS e auditoria |

## Como ler uma tabela

Cada tabela é documentada com o padrão abaixo:

```
┌────────────────────────────────────────────────────────────┐
│ TABELA: nome                                               │
│ Descrição de uma linha → papel no negócio                  │
└────────────────────────────────────────────────────────────┘
```

- **Colunas:** cada coluna é descrita com **tipo**, se é **PK/FK**, se é `NOT NULL`, valores **default** e **CHECK** aplicáveis.
- **Chave primária (PK):** identifica unicamente cada linha.
- **Chave estrangeira (FK):** `FK → tabela_alvo` com a ação de exclusão (`RESTRICT`/`CASCADE`/`SET NULL`).
- **Índices:** apenas os índices-chave são citados (há também índices de apoio a FKs e performance).
- **Triggers:** regras automatizadas disparadas em `INSERT`/`UPDATE`/`DELETE`.

Para a implementação SQL correspondente, consulte a **[Documentação do Script](../script/README.md)**.

### Notação usada nas tabelas de colunas

| Símbolo | Significado |
|---|---|
| 🔑 `PK` | Chave primária |
| 🔗 `FK→x` | Chave estrangeira (referencia a tabela `x`; ação de exclusão indicada junto) |
| 🔎 `UQ` | `UNIQUE` |
| ✅ `CK` | `CHECK` |
| `def` | Valor padrão (`DEFAULT`) |
| `NN` | `NOT NULL` |

## Escopo dos dados (visão geral)

- **2 schemas:** `mottainai` (operacional/OLTP) e `mottainai_analytics` (analítico/OLAP, views).
- **≈ 68 tabelas** operacionais + 3 arquivos de arquivamento (`_archive`, clones via `LIKE`).
- **24 tipos enum** para estados de negócio + estados restritos por `VARCHAR`/`CHECK`.
- **4 tabelas particionadas** por data (pedido, movimentação, venda, auditoria).
- **≈ 36 views analíticas** (5 utilitárias no schema `public` + ~30 no `mottainai_analytics`) e **1 view materializada** (`mv_dashboard_metrics`).

---

## Índice de Tabelas por Arquivo de Domínio

> Links acionáveis para a documentação completa de cada tabela.

- **02-cadastro-e-empresa.md:** `subscription_plan` · `company` · `retail_store` · `employee_role` · `employee` · `employee_private_data` · `app_user` · `staff_session` · `address`
- **03-produto-e-compras.md:** `product_category` · `tax_profile` · `product` · `supplier` · `supplier_product` · `purchase_order` · `purchase_order_item` · `receiving` · `receiving_item`
- **04-estoque.md:** `batch` · `inventory` · `inventory_movement` · `replenishment_pre_list` · `replenishment_pre_list_item` · `replenishment_execution` · `replenishment_execution_item`
- **05-vendas-pdv.md:** `customer` · `customer_auth` · `customer_consent` · `pos_terminal` · `pos_shift` · `pos_cash_movement` · `sales_transaction` · `sale_item` · `sale_payment` · `fiscal_document` · `pos_cancel_request`
- **06-fidelidade-promocoes.md:** `customer_geofence` · `loyalty_account` · `loyalty_transaction` · `loyalty_reward` · `loyalty_redemption` · `promotion` · `promotion_item`
- **07-inteligencia-motor.md:** `alert` · `suggested_action` · `ai_model` · `ai_prediction` · `ai_recommendation` · `ai_feedback` · `ai_execution` · `engine_scan_log` · `engine_suggestion` · `system_rule`
- **08-logistica-sustentabilidade.md:** `transfer` · `transfer_item` · `donation` · `donation_item` · `disposal` · `disposal_item`
- **09-auditoria-observabilidade.md:** `schema_version` · `audit_log` · `legacy_sync_record` · `system_log` · `error_log` · `integration_log` · `job_log` · `product_history` · `supplier_history` · `product_price_history` · `event_queue` · `kpi_cache` · `query_performance` · (arquivos `*_archive`)

---

*Última atualização: 2026-10-11 · Repositório: `Mottainai-Hub` → `Docs/banco/model-logico`*
