# Arquitetura de Segurança do Banco Operacional

> PostgreSQL 15+ · defesa em profundidade · multitenancy por empresa e loja

## Objetivo

Evitar acesso entre empresas, limitar o impacto de uma credencial comprometida,
proteger tokens e dados pessoais e manter evidência confiável das operações.
Segurança de banco complementa autenticação, autorização e validação realizadas
pela API; não substitui essas camadas.

## Papéis e responsabilidades

| Papel | Finalidade | Restrições principais |
|---|---|---|
| Proprietário/migrator | Instalar migrations e manter objetos | Nunca usado pela API |
| `mottainai_api` | Role de grupo usada durante requisições | `NOLOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOBYPASSRLS`, sem DDL |
| `mottainai_customer_api` | Role de grupo exclusiva do aplicativo do cliente | `NOLOGIN`, `NOBYPASSRLS`, sem acesso a auditoria ou integração legada |
| `mottainai_client_api` | Superfície final do backend mobile | `NOLOGIN`, somente views e funções autorizadas; sem escrita direta nas tabelas de autenticação e perfil |
| `mottainai_client_catalog_owner` | Dono técnico das views de catálogo | `NOLOGIN`, sem membership permanente no migrator |
| `mottainai_client_profile_owner` | Dono técnico das funções de perfil | `NOLOGIN`, acesso mínimo ao cadastro e envelope privado |
| `mottainai_client_auth_owner` | Dono técnico das funções de autenticação | `NOLOGIN`, acesso mínimo a `customer_auth` |
| `mottainai_migrator` | Importar dados tratados do legado | `NOLOGIN`, `NOINHERIT`, sem DDL, acesso somente às tabelas da integração |
| Login real da API | Autentica no PostgreSQL/Render | Deve ser membro de `mottainai_api` e usar `SET LOCAL ROLE` |
| Pipeline analítico | Consumir eventos confirmados | Credencial própria, sem acesso administrativo ao OLTP |

Nenhuma senha é criada pelos scripts. A associação do login real é feita pelo
administrador do ambiente:

```sql
GRANT mottainai_api TO nome_real_do_login_da_api;
```

O instalador aceita ambientes PostgreSQL gerenciados nos quais o migrator tem
`CREATEROLE`, mas não `SUPERUSER`. Atributos reservados (`SUPERUSER`,
`REPLICATION` e `BYPASSRLS`) são consultados em `pg_roles`: se estiverem
desativados, a instalação continua; se algum estiver ativo, o processo falha
fechado e exige correção por um administrador autorizado.

No Aiven, o provedor mantém nominalmente `avnadmin` como membro das roles que
ele cria. Essa associação administrativa é aceita somente para esse principal;
qualquer outro membro das roles `mottainai_client_*_owner` faz a migration
falhar. O login da API recebe exclusivamente a role pública do seu contrato.

## Contexto seguro por transação

O contexto contém `user_id`, `company_id` e `store_id`. Ele é obtido dos
relacionamentos reais entre `app_user`, `employee`, `retail_store` e `company`.
A API não informa livremente a empresa ou loja.

```sql
BEGIN;
SET LOCAL ROLE mottainai_api;
SELECT mottainai.fn_bootstrap_staff_context(:identity, :lookup);
-- comandos da requisição
COMMIT;
```

Valores válidos de `lookup`:

- `CPF`: login ativo por CPF;
- `EMAIL`: login ativo por e-mail;
- `INVITED_CPF`: primeira definição de senha de usuário convidado.

Para fluxos sem senha:

- `fn_bootstrap_staff_context_by_token`: recuperação de senha ou convite;
- `fn_bootstrap_staff_context_by_session`: renovação por sessão e hash do refresh token.

O setter antigo não é executável pela API. `SET`, `set_config` e permissões de
parâmetro também são revogados para `app.current_user_id`,
`app.current_company_id` e `app.current_store_id`. Isso impede falsificação do
tenant mesmo que uma consulta arbitrária alcance a conexão da API.

## Row Level Security

As políticas são atribuídas explicitamente à role `mottainai_api`.

| Perfil | Escopo de loja |
|---|---|
| `Administrator` | Todas as lojas ativas da empresa do usuário |
| Demais perfis | Somente `app.current_store_id` |

RLS protege cabeçalhos e tabelas filhas dos fluxos de estoque, compra,
recebimento, PDV, venda, promoção, transferência, doação, descarte e reposição.
`product` usa `company_id`: uma empresa pode possuir muitos produtos e cada
produto pertence a exatamente uma empresa.

Views da API usam `security_invoker=true`; portanto, não herdam o poder do dono
da view e continuam submetidas ao RLS do chamador.

## Credenciais, tokens e sessões

- senha e token de recuperação de baixa entropia são calculados pela API com BCrypt (`$2a$`, `$2b$` ou `$2y$`); o banco recebe somente o hash;
- refresh token e convite, gerados com alta entropia, são persistidos como SHA-256 prefixado;
- identificadores pessoais usados para busca são tokens SHA-256 prefixados, nunca o valor aberto;
- refresh deve rotacionar o hash a cada uso;
- logout preenche `revoked_at`, sem exclusão física;
- troca de senha revoga todas as sessões ativas do usuário;
- tentativa de reutilização de refresh token deve revogar a cadeia da sessão;
- tokens e hashes nunca aparecem em resposta, log ou evento.

## Contrato de dados protegidos

O banco operacional segue o contrato definido com o banco legado. Dados
compartilhados chegam pelo backend/RPA já mascarados, anonimizados ou
tokenizados. A integração registra apenas metadados e o checksum do payload em
`legacy_sync_record`; o payload pessoal bruto não é persistido.

Para registros novos, a API usa tokens versionados como
`CPF_SHA256_<64-hex>`, `EMAIL_SHA256_<64-hex>`, `PHONE_SHA256_<64-hex>` e
`AUTH_SHA256_<64-hex>`. Valores legados já aprovados, como `CPF_TKN_*`,
`EMAIL_EMP_*` e contatos mascarados, continuam aceitos durante a transição.
SHA-256 deve ser calculado pela aplicação com segredo do ambiente para campos
de baixa entropia. O banco valida formato e recusa dados abertos.

O módulo de clientes obedece ao mesmo princípio, mesmo sem origem no legado:

- nome, CPF, e-mail, telefone, UID externo e endereço são tokens protegidos;
- data de nascimento exata não é armazenada; somente `birth_year`;
- consentimentos são versionados e auditados em `customer_consent`;
- a role `mottainai_customer_api` usa `fn_bootstrap_customer_context` e só
  enxerga o próprio cliente por RLS.

O contexto RLS mobile é mantido em `api_customer_transaction_context`, não em
um parâmetro configurável pela conexão. A chave lógica é o PID do backend e a
linha só é válida quando `transaction_id = txid_current()`. A tabela pertence a
uma role técnica `NOLOGIN`; as roles de aplicação não recebem privilégios
diretos sobre ela.

Quando a aplicação precisa recuperar nome, CPF, e-mail ou telefone, armazena um
único payload `JSON_V1` em `customer_private_data`, cifrado pela aplicação com
AES-256-GCM. O banco guarda somente ciphertext, nonce de 12 bytes, versão da
chave, algoritmo e metadados; a chave permanece no KMS/secret manager. Tokens
determinísticos continuam separados e servem apenas para busca e unicidade.

O envelope usa `ON DELETE RESTRICT` e `deleted_at`: desativar ou excluir
logicamente o cliente retira o envelope das leituras normais sem destruir a
evidência cifrada. A API interna pode ler somente quando o funcionário ativo é
gerente/administrador e existe venda do cliente na mesma empresa. Sua única
escrita direta é `deleted_at`; nenhuma role de API recebe `DELETE` físico.

## Superfície isolada do aplicativo mobile

`mottainai_client_api` não consulta tabelas-base livremente. Catálogo, lojas,
promoções e fidelidade são publicados por views `security_barrier`. Cadastro,
alteração de perfil, login, recuperação e troca de senha passam por funções
`SECURITY DEFINER` com `search_path` fixo e donos técnicos `NOLOGIN` distintos.
Os donos são separados por domínio para que uma função comprometida não herde
acesso ao catálogo, perfil e autenticação ao mesmo tempo.

## Contexto controlado da RPA

O login técnico da automação recebe apenas membership em
`mottainai_migrator`. Em cada transação, a função
`fn_set_legacy_migration_context(company_id)` valida a empresa, habilita a
operação `legacy-import` e mantém RLS ativo. A role pode inserir ou atualizar
somente endereço, papel, plano, empresa, loja, funcionário, usuário e a trilha
de sincronização; não recebe DDL nem `BYPASSRLS`.

A auditoria não inventa `user_id = 0`: importações sem conta operacional
correspondente usam `NULL`, preservando empresa, transação e aplicação cliente.

Para funcionário, a RPA cifra separadamente nome, CPF, e-mail e telefone com
AES-256-GCM, nonce aleatório de 12 bytes e chave versionada externa. CPF e
e-mail recebem HMAC-SHA-256 com chave distinta para busca e unicidade. O banco
legado permanece somente leitura e não precisa adotar as tabelas privadas do
operacional.

## Auditoria

`audit_log` registra tabela, operação, registro, usuário, empresa, loja, IP,
aplicação cliente, transação e estados anterior/novo. Antes da gravação são
removidos recursivamente `password_hash`, hashes de token, documentos e dados
pessoais, inclusive quando estiverem aninhados em JSON.

A role da API possui somente leitura filtrada por empresa. Escrita, alteração,
exclusão e truncamento são proibidos; os triggers gravam por função
`SECURITY DEFINER` com `search_path` fixo. Uma escrita auditada da API sem
contexto validado falha em vez de continuar sem evidência.

## Controles fora do SQL

O ambiente deve complementar o banco com:

- TLS com certificado validado (`sslmode=verify-full` quando suportado);
- secret manager e rotação periódica de credenciais;
- pool configurado para iniciar e encerrar transação por requisição;
- backups criptografados, PITR e testes de restauração;
- alertas para falhas de login, violações de RLS e alterações de privilégios;
- atualização de PostgreSQL e extensões dentro da janela de suporte;
- retenção e anonimização alinhadas à LGPD e às obrigações fiscais.

## Checklist para produção

- [ ] PR de propriedade de produto por empresa aplicada.
- [ ] Migration de hardening aplicada e testes aprovados.
- [ ] Login real recebeu membership em `mottainai_api`.
- [ ] API usa transação e `SET LOCAL ROLE` por requisição.
- [ ] Senhas usam BCrypt; tokens aleatórios usam gerador criptográfico e SHA-256.
- [ ] Backends enviam somente valores compatíveis com o contrato protegido.
- [ ] Login do aplicativo cliente recebeu membership em `mottainai_customer_api`.
- [ ] Login do backend mobile recebeu somente membership em `mottainai_client_api`.
- [ ] Chaves AES e de lookup estão no secret manager, com versão e rotação documentadas.
- [ ] Exclusão de cliente foi testada como `UPDATE deleted_at`, nunca `DELETE` físico.
- [ ] Login da RPA recebeu somente membership em `mottainai_migrator`.
- [ ] TLS obrigatório e credenciais fora do código.
- [ ] Backup restaurado com sucesso em ambiente isolado.
- [ ] Alertas e retenção de auditoria configurados.
