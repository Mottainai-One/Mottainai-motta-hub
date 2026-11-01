# Instalação e Atualização

## Pré-requisitos

- PostgreSQL 15 ou superior;
- `psql` disponível;
- permissão para extensões, schemas e roles na instalação;
- bancos físicos `mottainai_operational` e `mottainai_analytics`;
- backup validado antes de atualizar uma base existente.

Em um PostgreSQL gerenciado, o usuário de migration pode ter `CREATEROLE` sem
ser `SUPERUSER`. O instalador não tenta alterar atributos reservados; ele
verifica que as roles de API não possuem `SUPERUSER`, `REPLICATION` ou
`BYPASSRLS` e interrompe com uma mensagem segura se encontrar configuração
privilegiada.

## Instalação nova

Clone o repositório `Mottainai-Banco-Operacional` e execute:

```bash
psql -v ON_ERROR_STOP=1 \
  -d mottainai_operational \
  -f database/operational/install.sql
```

Depois instale o banco analítico:

```bash
psql -v ON_ERROR_STOP=1 \
  -d mottainai_analytics \
  -f database/analytics/install.sql
```

Os instaladores usam `\ir`; por isso devem ser executados pelo `psql` ou por
uma ferramenta de migration configurada na mesma ordem.

## Atualização de base existente

O atualizador consolidado executa os módulos de produto, segurança, dados
sensíveis, compatibilidade JPA e contrato API/RPA na ordem segura e em uma
única transação:

```bash
psql -v ON_ERROR_STOP=1 -d mottainai_operational \
  -f database/operational/update_existing_api_rpa.sql
```

Para uma base que já contém os módulos anteriores e precisa somente do contrato
final de dados privados do cliente e da API mobile, execute:

```bash
psql -v ON_ERROR_STOP=1 -d mottainai_operational \
  -f database/operational/update_existing_customer_private_data.sql
```

O atualizador executa os módulos 37 e 38 em uma transação. Em caso de erro,
nenhuma alteração parcial é confirmada.

### Migração de dados pessoais de funcionários

A remoção das colunas legadas não pode ocorrer na mesma transação que prepara
o cofre. O fluxo obrigatório é:

1. aplicar `28_reversible_employee_pii.sql` e confirmar a criação de
   `employee_private_data`;
2. executar a RPA/backend com as chaves do secret manager para produzir os
   envelopes AES-256-GCM e HMACs de busca;
3. associar `firebase_uid` real às contas ativas ou mantê-las inativas enquanto
   forem convites pendentes;
4. validar que não existem registros `MIGRATION_PENDING`;
5. aplicar `29_finalize_reversible_employee_pii.sql` para remover
   `employee.name/cpf/email/phone` e `app_user.cpf/email`.

O banco legado não recebe essa mudança estrutural. A RPA transforma os dados ao
gravá-los no operacional. Um valor já mascarado ou irreversível na origem não
se torna recuperável por ser cifrado novamente.

Se um produto antigo estiver ligado a mais de uma empresa, a migration para
sem escolher um tenant arbitrariamente. Duplique o cadastro por empresa,
redirecione as referências operacionais e reaplique o script.

Depois da atualização, execute `11_product_company_tests.sql` e
`26_api_rpa_compatibility_tests.sql`. Associe os logins reais às roles de grupo
fora do repositório:

```sql
GRANT mottainai_api TO login_real_da_api;
GRANT mottainai_customer_api TO login_real_do_app_cliente;
GRANT mottainai_migrator TO login_real_da_rpa;
GRANT mottainai_client_api TO login_real_do_backend_mobile;
```

A RPA deve iniciar uma transação, usar `SET LOCAL ROLE mottainai_migrator`,
chamar `fn_set_legacy_migration_context(company_id)`, executar os upserts e
encerrar o contexto antes do `COMMIT`.

## Partições mensais

O operacional mantém 12 meses anteriores, o mês atual e 6 futuros para:

- `purchase_order` por `order_date`;
- `inventory_movement` por `movement_date`;
- `sales_transaction` por `sale_date`;
- `audit_log` por `operation_date`.

O analítico usa a mesma janela inicial nas quatro maiores tabelas de fatos.
Execute a manutenção antes da virada do mês e monitore partições default no
analítico.

## Validação pós-instalação

- confirmar versões em `mottainai.schema_version`;
- confirmar que `mottainai_api` não tem `BYPASSRLS`;
- confirmar que `mottainai_customer_api` não acessa auditoria ou integração legada;
- testar dois tenants distintos com a role da API;
- testar dois clientes distintos com a role exclusiva do aplicativo;
- testar login, refresh, logout e revogação por troca de senha;
- verificar que valores abertos são recusados e auditoria aninhada é sanitizada;
- medir poda de partição com `EXPLAIN (ANALYZE, BUFFERS)`;
- confirmar ingestão idempotente no banco analítico;
- confirmar as dez views `vw_api_*` e as funções transacionais da API;
- confirmar as views mobile com `security_barrier` e as funções de perfil/autenticação;
- em Aiven, confirmar que somente `avnadmin` permaneceu como membro técnico das
  roles owner criadas pelo provedor; nenhum login de aplicação pode recebê-las;
- confirmar que `api_customer_transaction_context` é inacessível diretamente
  às roles das APIs e que o contexto expira ao trocar de transação;
- testar desativação do cliente, exclusão lógica do envelope e bloqueio do `DELETE` físico;
- testar uma importação RPA com auditoria e `user_id` nulo.
