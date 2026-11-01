# 10 — Banco Analítico

O analítico é um **PostgreSQL físico separado**, chamado
`mottainai_analytics`, com schema principal de mesmo nome. Ele não participa do
commit de venda, estoque ou caixa e não consulta o operacional por `dblink`.

## Modelo

O banco usa modelo estrela. Dimensões descrevem empresa, loja, produto,
categoria, fornecedor, funcionário, cliente anonimizado, lote e calendário.
Fatos preservam medidas no grão documentado.

| Fato | Grão |
|---|---|
| `fact_sales` | Uma venda por data |
| `fact_sale_item` | Um item de venda por data |
| `fact_inventory_movement` | Uma movimentação de estoque por data |
| `fact_inventory_snapshot` | Posição diária por loja, produto, lote e tipo |
| `fact_purchase_order` | Um pedido por data |
| `fact_receiving` | Um recebimento |
| `fact_promotion_result` | Promoção por loja, produto e dia |
| `fact_loss_destination` | Uma destinação de perda |
| `fact_transfer` | Uma transferência |
| `fact_replenishment` | Uma reposição |
| `fact_loyalty` | Um evento de pontos |

As quatro primeiras tabelas são particionadas mensalmente, com partição default
para impedir perda de carga fora da janela preparada.

## Ingestão

```text
event_queue operacional
        |
        v
ingestion_event -> validação -> dimensões -> fatos -> checkpoint
        |                                      |
        +-> etl_dead_letter                    +-> views e KPIs
```

- `event_uuid` garante idempotência;
- checkpoint avança somente depois do commit completo;
- payload inválido ou incompatível segue para dead letter;
- replay conserva o UUID original;
- IDs operacionais são correlação, não FK entre databases.

## Privacidade

- `dim_customer` expõe `anonymous_key`, nunca CPF, nome, e-mail ou telefone;
- `dim_employee` não replica CPF;
- dashboards usam role somente leitura;
- payload bruto de ingestão e features de modelo não são expostos à API;
- reconciliação diária compara vendas, valores e snapshots com o operacional.

## Instalação

```bash
psql -v ON_ERROR_STOP=1 \
  -d mottainai_analytics \
  -f database/analytics/install.sql
```

Consulte também o [guia operacional](../operacao/README.md).

Para montar ou revisar o tracking, use o
[dicionário analítico para tracking](../tracking/02-banco-analitico-para-tracking.md),
que documenta campos, grãos, objetos derivados, ingestão e exclusões de PII.
