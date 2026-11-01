# 03 — Produto e Compras

Domínio do **catálogo de produtos** (SKUs) e do **ciclo de compra e recebimento** (do pedido ao lote).

```
company ──< product >── product_category / tax_profile
supplier >──< product    (associação many-to-many: supplier_product)
store ──< purchase_order >── supplier / employee
purchase_order ──< purchase_order_item ──> product
purchase_order ──< receiving ──< receiving_item ──➤ (gera lote via trigger trg_create_batch)
```

## `product_category`

Agrupamento de produtos (mercearia, bebidas, carnes, limpeza…).

| Coluna | Tipo | Restrições |
|---|---|---|
| `category_id` 🔑 | `INTEGER` identity | `PK` |
| `name` 🔎 | `VARCHAR(100)` | `NN` `UQ` |
| `description` | `TEXT` | |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

## `tax_profile`

Perfil tributário de um produto (parâmetros fiscais para emissão de documentos).

| Coluna | Tipo | Restrições |
|---|---|---|
| `tax_profile_id` 🔑 | `INTEGER` identity | `PK` |
| `code` 🔎 | `VARCHAR(30)` | `NN` `UQ` |
| `name` | `VARCHAR(120)` | `NN` |
| `description` | `TEXT` | |
| `cfop` | `VARCHAR(4)` | |
| `icms_cst` / `icms_csosn` | `VARCHAR(3)` / `VARCHAR(4)` | |
| `icms_rate` ✅ | `DECIMAL(7,4)` | `def 0` `CHECK 0..100` |
| `ipi_cst` / `ipi_rate` | `VARCHAR` / `DECIMAL` | |
| `pis_cst` / `pis_rate` | `VARCHAR` / `DECIMAL` | |
| `cofins_cst` / `cofins_rate` | `VARCHAR` / `DECIMAL` | |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

## `product` (SKU)

Item comercializado e pertencente a uma empresa. Carrega o custo médio (`avg_cost`) e o preço sugerido (`suggested_price`) recalculados automaticamente (RF16).

| Coluna | Tipo | Restrições |
|---|---|---|
| `product_id` 🔑 | `INTEGER` identity | `PK` |
| `company_id` 🔗 | `INTEGER` | `NN` `FK → company(company_id) ON DELETE RESTRICT` |
| `category_id` 🔗 | `INTEGER` | `NN` `FK → product_category(…) ON DELETE RESTRICT` |
| `tax_profile_id` 🔗 | `INTEGER` | `NN` `FK → tax_profile(…) ON DELETE RESTRICT` |
| `sku` 🔎 | `VARCHAR(50)` | `NN` `UQ (company_id, sku)` |
| `barcode` 🔎 | `VARCHAR(30)` | `NN` `UQ (company_id, barcode)` |
| `ncm` ✅ | `VARCHAR(8)` | `NN` `CHECK ^\d{8}$` |
| `cest` ✅ | `VARCHAR(7)` | `CHECK ^\d{7}$` |
| `name` | `VARCHAR(150)` | `NN` |
| `description` | `TEXT` | |
| `brand` | `VARCHAR(100)` | |
| `unit_measure` | `VARCHAR(20)` | `NN` |
| `weight` ✅ | `DECIMAL(10,3)` | `CHECK ≥ 0` |
| `active` | `BOOLEAN` | `def TRUE` |
| `version` | `INTEGER` | `def 1` |
| `avg_cost` ✅ | `DECIMAL(10,2)` | `def 0` `CHECK ≥ 0` |
| `suggested_price` ✅ | `DECIMAL(10,2)` | `CHECK ≥ 0` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |

**Triggers:**
- `trg_product_generate_sku` (_BEFORE INSERT_) — gera SKU automático se vazio/duplicado.
- `trg_product_update_sku` (_BEFORE UPDATE_) — regenera SKU se empresa/nome/categoria/marca mudarem.
- `trg_soft_delete_product` (_BEFORE UPDATE OF active_) — define `active=false` + `deleted_at` na desativação.
- `trg_product_history` (_BEFORE UPDATE_) — registra mudanças em `product_history`.

**Segurança:** `product_policy` aplica RLS por `company_id`. Empresas diferentes podem usar o mesmo SKU ou código de barras sem colisão.

## `supplier`

Fornecedor de mercadorias.

| Coluna | Tipo | Restrições |
|---|---|---|
| `supplier_id` 🔑 | `INTEGER` identity | `PK` |
| `address_id` 🔗 | `INTEGER` | `NN` `FK → address(…) ON DELETE RESTRICT` |
| `trade_name` | `VARCHAR(150)` | `NN` |
| `cnpj` | `CHAR(14)` | `NN` `UQ` `CHECK fn_validate_cnpj` |
| `email` / `phone` | `VARCHAR` | mascarados no formato legado ou tokens SHA-256 prefixados |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

## `supplier_product`

Associação **many-to-many** entre fornecedor e produto, com condições comerciais.

| Coluna | Tipo | Restrições |
|---|---|---|
| `supplier_product_id` 🔑 | `INTEGER` identity | `PK` |
| `supplier_id` 🔗 | `INTEGER` | `NN` `FK → supplier(…)` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(…)` |
| `supplier_code` | `VARCHAR` | |
| `purchase_price` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `lead_time` ✅ | `INTEGER` | `NN` `CHECK ≥ 0` |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |
| 🔎 `UQ` | | `(supplier_id, product_id)` |

## `purchase_order`

Pedido de compra de mercadorias para uma loja. **Tabela particionada por `order_date`** (PK composta).

| Coluna | Tipo | Restrições |
|---|---|---|
| `purchase_order_id` 🔑 | `INTEGER` identity | parte da `PK (purchase_order_id, order_date)` |
| `order_date` 🔑 | `TIMESTAMP` | parte da PK · coluna de partição |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(…)` |
| `supplier_id` 🔗 | `INTEGER` | `NN` `FK → supplier(…)` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(…)` |
| `expected_delivery_date` | `DATE` | |
| `status` | `purchase_order_status` | `def PENDING` |
| `observation` | `TEXT` | |
| `total_amount` ✅ | `DECIMAL(12,2)` | `def 0` `CHECK ≥ 0` |
| `version` | `INTEGER` | |
| timestamps | `TIMESTAMP` | |

**Observações:** sujeita a **RLS**.

## `purchase_order_item`

Itens (linhas) do pedido de compra.

| Coluna | Tipo | Restrições |
|---|---|---|
| `purchase_order_item_id` 🔑 | `INTEGER` identity | `PK` |
| `purchase_order_id` 🔗 + `order_date` | `INTEGER` + `TIMESTAMP` | `NN` `FK → purchase_order(…) ON DELETE CASCADE` |
| `product_id` 🔗 | `INTEGER` | `NN` `FK → product(…)` |
| `requested_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK > 0` |
| `unit_price` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `subtotal` | `DECIMAL(12,2)` | **gerado** — `(requested_quantity * unit_price) STORED` |
| `deleted_at` | `TIMESTAMP` | exclusão lógica usada pelas views da API |

O item não possui `company_id`; as views e políticas derivam o tenant do
pedido de compra e da loja correspondente.

## `receiving`

Conferência/entrada da mercadoria do pedido (padrão da nota fiscal).

| Coluna | Tipo | Restrições |
|---|---|---|
| `receiving_id` 🔑 | `INTEGER` identity | `PK` |
| `purchase_order_id` 🔗 + `order_date` | `INTEGER` + `TIMESTAMP` | `NN` `FK → purchase_order(…) ON DELETE RESTRICT` |
| `employee_id` 🔗 | `INTEGER` | `NN` `FK → employee(…)` |
| `receiving_date` | `TIMESTAMP` | `def NOW()` |
| `status` | `receiving_status` | `def PENDING` |
| `observation` | `TEXT` | |
| timestamps | `TIMESTAMP` | |

## `receiving_item`

Item recebido, com data de fabricação e **validade**. Ao inserir, o trigger **gera automaticamente um lote** (`trg_create_batch`) — base da entrada de estoque e do cálculo de custo médio.

| Coluna | Tipo | Restrições |
|---|---|---|
| `receiving_item_id` 🔑 | `INTEGER` identity | `PK` |
| `receiving_id` 🔗 | `INTEGER` | `NN` `FK → receiving(…) ON DELETE CASCADE` |
| `purchase_order_item_id` 🔗 | `INTEGER` | `NN` `FK → purchase_order_item(…) ON DELETE RESTRICT` |
| `received_quantity` ✅ | `DECIMAL(10,3)` | `NN` `CHECK ≥ 0` |
| `unit_price` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `manufacture_date` | `DATE` | |
| `expiration_date` | `DATE` | `NN` |
| `observation` | `TEXT` | |
| ✅ `CHECK` | | `manufacture_date ≤ expiration_date` |

**Trigger:** `trg_create_batch` (_AFTER INSERT_) — cria o lote correspondente.

---

*Próximo: [04 — Estoque](04-estoque.md)*
