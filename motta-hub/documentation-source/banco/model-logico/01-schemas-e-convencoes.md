# 01 — Schemas e Convenções

## Os dois bancos físicos

O ecossistema usa **dois bancos PostgreSQL independentes**, evitando concorrência entre OLTP e BI:

| Database | Schema | Tipo | Responsabilidade |
|---|---|---|---|
| `mottainai_operational` | `mottainai` | Operacional (OLTP) | Cadastros e transações oficiais |
| `mottainai_analytics` | `mottainai_analytics` | Analítico (OLAP) | Dimensões, fatos, histórico, BI e IA |

Não existem FKs, `dblink` ou commits distribuídos entre databases. A integração é assíncrona e idempotente por eventos confirmados.

## Extensões habilitadas

| Extensão | Uso |
|---|---|
| `uuid-ossp` | Geração de UUIDs |
| `pgcrypto` | Funções criptográficas (hash de senha, tokens) |
| `btree_gist` | Restrições de exclusão por intervalo de vigência de preço |

## Convenções de projeto

### 1. Nomenclatura
- **Tabelas:** `snake_case`, semântica em inglês (ex.: `retail_store`, `sale_item`).
- **Colunas:** `snake_case`; chaves primárias seguem o padrão `<entidade>_id`.
- **Chaves estrangeiras:** colunas nomeadas conforme a tabela alvo (`store_id → retail_store`, `product_id → product`).
- **Enums (tipos):** `snake_case` (ex.: `sale_status`, `priority_level`).
- **Funções/views:** prefixo por tipo — `fn_*` (funções), `sp_*` (procedures), `trg_*` (triggers), `vw_*` (views).
- **Índices:** prefixo `idx_` (e `idx_unique_` para índices únicos).

### 2. Soft delete (exclusão lógica)
A maioria das tabelas de cadastro e transações mantém a linha mesmo após "exclusão", usando as colunas:
- `active BOOLEAN` — controla se o registro está ativo.
- `deleted_at TIMESTAMP` — marca lógica de exclusão (torna `active = FALSE` via trigger).
- `updated_at TIMESTAMP` — última atualização.

> **Benefício:** preserva rastreabilidade e FKs históricas sem quebrar referências.

### 3. Controle de concorrência otimista
Tabelas com atualização concorrente carregam a coluna `version INTEGER` (ex.: `product`, `purchase_order`, `inventory`, `sales_transaction`, `transfer`, `donation`, `disposal`). A função `fn_atomic_update_inventory` usa o `version` para detectar conflitos de escrita no estoque.

### 4. Particionamento por data
Quatro tabelas de alto volume são **particionadas por faixa de data** (PK composta inclui a coluna de data):

| Tabela | Coluna de partição |
|---|---|
| `purchase_order` | `order_date` |
| `inventory_movement` | `movement_date` |
| `sales_transaction` | `sale_date` |
| `audit_log` | `operation_date` |

As procedures `sp_create_future_partitions()` e `sp_drop_old_partitions(months)` gerenciam a criação (mês atual em diante) e a retenção de partições antigas.

### 5. Enums como domínios de estado
Todos os principais fluxos (compra, venda, estoque, promoção, IA, eventos, logs) usam **tipos enum** (ver `11-enums.md`) para garantir valores válidos. Alguns estados restritos usam `CHECK` inline com `VARCHAR` (documentados nas respectivas tabelas).

### 6. Segurança — roles e Row Level Security
`mottainai_api` e `mottainai_customer_api` são roles sem login e sem privilégios administrativos. A primeira isola empresa/loja; a segunda isola cada cliente. Os contextos são validados por funções `SECURITY DEFINER`, duram uma transação e não podem ser alterados diretamente pela API.

### 7. Auditoria e rastreabilidade
- Triggers de auditoria cobrem entidades sensíveis, sessões, tokens e transações operacionais.
- Triggers de histórico em `product` gravam mudanças em `product_history`.
- Cálculos de custo médio/preço sugerido são registrados em `product_price_history`.
- Auditoria registra empresa, loja, IP, aplicação e transação, removendo recursivamente documentos, identificadores e hashes do JSON.
- `fn_set_session_context` não é executável pela API; os bootstraps validados definem o contexto.

### 8. Regras de integridade e validação
- **Dados pessoais:** CPF, nome, e-mail, telefone, UID externo, endereço e documento fiscal são armazenados apenas em formatos protegidos e prefixados.
- **Segredos:** senhas e recuperação de baixa entropia usam BCrypt; tokens aleatórios de sessão/convite usam SHA-256.
- **Estoque:** impedimento de estoque negativo no nível de aplicação (`fn_atomic_update_inventory`) e por `CHECK` em colunas de quantidade.
- **Seleção de FEFO:** `fn_select_batch_fefo` escolhe o lote com menor validade, disparado pelo trigger `trg_select_batch_fefo` na criação de item de venda.

## Mapa de instalação dos scripts

Ordem de criação do banco (`install.sql`):

```
00 Database → 01 Enums → 02 Functions → 03 Tables → 04 Additional Tables →
04 Security → 05 Indexes → 06 Triggers → 07 Views → 08 Procedures →
08 Partition Fix → 09 Seed → 10 Product Company → 10 Tests →
11 Product Tests → 20 Security Hardening → 21 Security Tests →
22 Sensitive Data Contract → 23 Sensitive Data Contract Tests
```

> `database/operational/install.sql` é a fonte atual de instalação. O `dataLoad.sql` legado é exclusivo de teste e nunca roda em produção.

---

*Próximo: [02 — Cadastro e Empresa](02-cadastro-e-empresa.md)*
