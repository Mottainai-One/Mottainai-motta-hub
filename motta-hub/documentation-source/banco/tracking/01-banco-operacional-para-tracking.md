# Banco operacional — referência para tracking

Este documento é a fonte de referência para representar o banco operacional no
tracking centralizado. O tracking deve descrever o contrato físico vigente; não
deve transformar tabelas em eventos de produto quando não existe disparo de
frontend ou backend.

## Identificação

| Item | Valor |
|---|---|
| Database físico | `MOTTAINAI` / `mottainai_operational` conforme o ambiente |
| Schema principal | `mottainai` |
| Natureza | OLTP, transacional, multitenant |
| Chave do tenant | `company_id` |
| Exclusão lógica | `deleted_at`, quando presente |
| Particionamento mensal | vendas, movimentos, pedidos e auditoria de alto volume |
| Origem anterior | banco legado, por RPA a cada 30 minutos |
| Destino posterior | banco analítico, carga diária às 02:00 de Brasília |

## Como preencher o tracking

| Coluna do tracking | Conteúdo correto para banco |
|---|---|
| `ID do Contrato` | `mottainai.<tabela>` |
| `Nome do Evento` | nome físico da tabela; não implica evento instrumentado |
| `Descrição do Evento` | finalidade e grão da tabela |
| `Momento do disparo` | operação que grava a linha, apenas quando conhecida |
| `Nome Propriedade` | nome físico da coluna |
| `Descrição Propriedade` | significado funcional da coluna |
| `Tipagem` | tipo PostgreSQL efetivo |
| `Obrigatório` | `sim` somente para `NOT NULL` |
| `Complemento sobre o valor` | PK, FK, UNIQUE, CHECK, default, enum e política de proteção |
| `Plataforma` | `PostgreSQL / Operacional` |
| `Métrica` | preencher somente quando a coluna for uma medida de negócio |
| `Data Lake Table` | objeto analítico de destino, quando existir |

## Domínios e fontes dos campos

| Contexto | Tabelas principais | Fonte detalhada |
|---|---|---|
| Empresa e unidades | `subscription_plan`, `company`, `retail_store`, `address` | [02 — Cadastro e empresa](../model-logico/02-cadastro-e-empresa.md) |
| Equipe e acesso | `employee_role`, `employee`, `employee_private_data`, `app_user`, `staff_session`, `password_reset_token` | [02 — Cadastro e empresa](../model-logico/02-cadastro-e-empresa.md) |
| Catálogo e compras | categorias, produtos, tributos, fornecedores, pedidos e recebimentos | [03 — Produto e compras](../model-logico/03-produto-e-compras.md) |
| Estoque | lotes, estoque, movimentos e contagens | [04 — Estoque](../model-logico/04-estoque.md) |
| PDV e vendas | terminais, turnos, caixa, vendas, itens, pagamentos e fiscal | [05 — Vendas e PDV](../model-logico/05-vendas-pdv.md) |
| Clientes e fidelidade | cliente, cofre privado, consentimentos, geocerca e fidelidade | [06 — Fidelidade e promoções](../model-logico/06-fidelidade-promocoes.md) |
| IA e motor | alertas, ações sugeridas e regras | [07 — Inteligência e motor](../model-logico/07-inteligencia-motor.md) |
| Logística | transferências, doações, descarte e reposição | [08 — Logística](../model-logico/08-logistica-sustentabilidade.md) |
| Governança | auditoria, logs, jobs, eventos e históricos | [09 — Auditoria](../model-logico/09-auditoria-observabilidade.md) |

## Contrato final de dados pessoais

Este bloco substitui qualquer versão anterior do tracking.

| Entidade | Pode aparecer no tracking | Não pode permanecer como coluna aberta |
|---|---|---|
| `employee` | IDs, loja, papel, HMAC de busca, datas e estado | nome, CPF, e-mail e telefone |
| `employee_private_data` | ciphertext, nonce, máscara, versão da chave, algoritmo e estado | valor pessoal em texto claro |
| `app_user` | funcionário, BCrypt, Firebase UID, convite e datas | CPF e e-mail |
| `customer` | IDs técnicos, chave protegida, consentimento e estado | nome, CPF, e-mail e telefone |
| `customer_private_data` | envelope AES-256-GCM e metadados criptográficos | payload pessoal aberto |

Os cofres privados são relacionamentos 1:1. Ciphertext não é hash: pode ser
recuperado somente pela aplicação autorizada, com chave externa. HMAC serve
somente para busca/unicidade e não é reversível. Senhas usam BCrypt.

## Regras estruturais obrigatórias

- toda tabela multitenant chega a `company_id` diretamente ou por relação
  inequívoca;
- `product` pertence a uma empresa e unicidades comerciais consideram empresa;
- `firebase_uid` pode ser nulo em convite pendente; conta ativa exige UID;
- RLS e roles são controles físicos, não eventos de tracking;
- views `vw_api_*` são contratos derivados de leitura da API;
- tabelas privadas, credenciais e sessões nunca seguem para o analítico;
- IDs entre databases são correlação, não FK física.

## Relações centrais

```text
company 1 ── N retail_store 1 ── N employee 1 ── 0..1 app_user
                                  └── 1 employee_private_data
company 1 ── N product
retail_store 1 ── N inventory N ── 1 product
purchase_order 1 ── N purchase_order_item
purchase_order 1 ── N receiving 1 ── N receiving_item
sales_transaction 1 ── N sale_item
sales_transaction 1 ── N sale_payment
customer 1 ── 1 customer_private_data
customer 1 ── N loyalty_transaction
```

## Critério de aceite

O tracking só está alinhado quando não contém PII aberta em `employee` ou
`app_user`, inclui os cofres privados, registra `company_id` em produto, mantém
as cardinalidades e diferencia tabela, view, enum e evento real.

