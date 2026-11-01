# Estrutura e Dependências dos Scripts

## Fluxo de criação

```text
infraestrutura
  -> tipos
  -> funções sem dependência de tabela
  -> tabelas principais
  -> tabelas adicionais
  -> segurança básica
  -> índices
  -> triggers
  -> views
  -> procedures e partições
  -> seed mínimo
  -> produto por empresa
  -> testes gerais e de produto
  -> hardening profissional
  -> testes de segurança
  -> contrato de dados sensíveis
  -> testes do contrato
  -> compatibilidade JPA
  -> contrato API/RPA
  -> testes API/RPA
  -> fixture de reinstalação protegida
  -> identidade reversível de funcionários
  -> dados privados reversíveis de clientes
  -> migrations do PDV
  -> contrato isolado da API mobile
```

## Migrations recentes

### Produto por empresa

`10_product_company.sql` adiciona `product.company_id`, descobre a empresa por
preço, estoque, compra, venda, promoção e reposição, troca unicidades globais
por `(company_id, sku)` e `(company_id, barcode)`, atualiza geração de SKU e
ativa RLS. A migration não inventa propriedade em caso de conflito.

### Hardening de segurança

`20_security_hardening.sql` adiciona:

- role de grupo `mottainai_api` sem login e sem privilégios administrativos;
- `app_user.password_set` e finalidade dos tokens;
- `staff_session` com refresh token hash, expiração e revogação;
- bootstraps validados por login, token e sessão;
- proteção dos parâmetros de contexto contra `SET` e `set_config`;
- RLS em cabeçalhos, itens e entidades críticas;
- `security_invoker=true` nas views da API;
- auditoria por tenant, imutável e sanitizada;
- limites de timeout e grants mínimos.

### Contrato de dados sensíveis

`22_sensitive_data_contract.sql` estabelece os formatos SHA-256 e BCrypt,
converte valores abertos preexistentes, protege o módulo de clientes, cria
`customer_consent` e `legacy_sync_record`, adiciona a role exclusiva do
cliente e sanitiza logs JSON de forma recursiva. O RPA conserva somente
metadados e checksum, nunca o payload pessoal bruto.

### Contrato API e RPA

`25_api_rpa_compatibility.sql` adiciona os campos e enums exigidos pela API,
as dez views `vw_api_*`, funções de idempotência, pedido, recebimento e estoque,
RLS de monitoramento e a role `mottainai_migrator`. A RPA define a empresa por
`fn_set_legacy_migration_context`, sem receber `BYPASSRLS`; a auditoria mantém
`user_id = NULL` quando o legado não possui usuário operacional correspondente.

### Dados privados e API mobile

`37_reversible_customer_pii.sql` finaliza o envelope AES-256-GCM de clientes,
troca a remoção em cascata por `ON DELETE RESTRICT`, sincroniza a exclusão
lógica e limita a leitura interna a gestores autorizados da mesma empresa.

`38_client_mobile_api.sql` publica catálogo por views com barreira de segurança
e encapsula perfil, Firebase, login e recuperação em funções com donos técnicos
`NOLOGIN` separados. A role mobile não recebe escrita direta nas tabelas-base.

## Reaplicação

As migrations recentes podem ser reaplicadas. `CREATE ... IF NOT EXISTS`,
`DROP POLICY IF EXISTS`, verificações no catálogo e `ON CONFLICT` evitam
duplicação. Reaplicar não substitui backup nem revisão do plano de migration.

## Testes

| Arquivo | Verifica |
|---|---|
| `10_tests.sql` | Tabelas obrigatórias, separação física e partições |
| `11_product_company_tests.sql` | FK, índice, unicidades por empresa, RLS e SKU |
| `21_security_hardening_tests.sql` | Atributos da role, parâmetros protegidos, RLS, views e auditoria imutável |
| `23_sensitive_data_contract_tests.sql` | Formatos SHA-256/BCrypt, ausência de data exata, role do cliente, RLS e sanitização aninhada |
| `26_api_rpa_compatibility_tests.sql` | Views, funções, enums, privilégios, outbox idempotente, contexto da RPA, auditoria, pedido e recebimento |

O mesmo arquivo também verifica o contrato final mobile: comandos das políticas
RLS, FK restritiva, roles não privilegiadas, ausência de membership residual,
views com `security_barrier`, assinaturas das funções e exclusão lógica.

Além da suíte estrutural, a validação de release deve testar dois tenants,
sessão, revogação, auditoria sanitizada e tentativa de falsificação de contexto.
