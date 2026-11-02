# Campos inferidos do catálogo

O tracking e o material disponível não contêm DDL físico para duas tabelas. Para que o Hub não as mostre vazias, o importador propõe os campos abaixo. Cada descrição exibida no Hub começa com **INFERIDO — proposta para validação; não confirmado por DDL**.

Não use estas propostas para criar ou alterar tabelas em bancos de produção antes da validação do DDL oficial.

## `mottainai.inventory_count`

O tracking lista a tabela sem campos físicos. O modelo lógico descreve `inventory_count_item` e sua referência a `inventory_count`, mas não define a estrutura do cabeçalho da contagem.

| Campo proposto | Tipo sugerido | Restrições sugeridas |
| --- | --- | --- |
| `inventory_count_id` | `BIGSERIAL` | PK |
| `store_id` | `INTEGER` | NOT NULL; FK para `retail_store(store_id)` |
| `employee_id` | `INTEGER` | FK para `employee(employee_id)`; responsável pela contagem |
| `status` | `VARCHAR(30)` | NOT NULL; valores sugeridos: `IN_PROGRESS`, `COMPLETED`, `CANCELED` |
| `started_at` | `TIMESTAMPTZ` | NOT NULL; DEFAULT CURRENT_TIMESTAMP |
| `completed_at` | `TIMESTAMPTZ` | nullable; preenchido ao concluir |
| `created_at` | `TIMESTAMPTZ` | NOT NULL; DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL; atualizado em cada alteração |

## `mottainai.legacy_sync_record`

O modelo lógico descreve a finalidade e as informações conceituais registradas, mas não declara nomes, tipos ou restrições físicos. O payload bruto não deve ser armazenado.

| Campo proposto | Tipo sugerido | Restrições sugeridas |
| --- | --- | --- |
| `legacy_sync_record_id` | `BIGSERIAL` | PK |
| `source_system` | `VARCHAR(100)` | NOT NULL |
| `source_record_id` | `TEXT` | NOT NULL; identificador técnico na origem |
| `target_system` | `VARCHAR(100)` | NOT NULL |
| `target_record_id` | `TEXT` | identificador técnico no destino |
| `status` | `VARCHAR(30)` | NOT NULL |
| `synchronized_at` | `TIMESTAMPTZ` | NOT NULL |
| `payload_sha256` | `CHAR(64)` | NOT NULL; hash do payload tratado |

## Validação pendente

Confirmar nomes, tipos, nulabilidade, chaves, índices, valores de status e política de retenção com o DDL oficial. Quando esse DDL estiver disponível, substitua as propostas no importador pelo contrato confirmado.
