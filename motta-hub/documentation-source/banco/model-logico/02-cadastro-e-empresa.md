# 02 — Cadastro e Empresa

Domínio **multitenant (SaaS)** do Mottainai. Define o locatário (empresa), suas unidades (lojas), a hierarquia de funcionários, os usuários de acesso e os endereços reutilizados em todo o sistema.

```
subscription_plan ──< company ──< retail_store ──< employee ── 1:1 ── app_user ──< staff_session
                                                      └── 1:1 employee_private_data
                      │                │
                      │                └──< address
                      └──< address
(employee também referencia retail_store e employee_role)
```

## `subscription_plan`

Tipo de assinatura SaaS oferecida a uma empresa.

| Coluna | Tipo | Restrições |
|---|---|---|
| `plan_id` 🔑 | `INTEGER` identity | `PK` |
| `name` 🔎 | `VARCHAR(100)` | `NN` `UQ` |
| `description` | `TEXT` | |
| `price` ✅ | `DECIMAL(10,2)` | `NN` `CHECK ≥ 0` |
| `store_limit` ✅ | `INTEGER` | `NN` `CHECK > 0` |
| `user_limit` ✅ | `INTEGER` | `NN` `CHECK > 0` |
| `active` | `BOOLEAN` | `def TRUE` |
| `created_at` / `updated_at` / `deleted_at` | `TIMESTAMP` | |

## `company`

A empresa é o **locatário** do sistema SaaS e dono de uma ou mais lojas.

| Coluna | Tipo | Restrições |
|---|---|---|
| `company_id` 🔑 | `INTEGER` identity | `PK` |
| `plan_id` 🔗 | `INTEGER` | `NN` `FK → subscription_plan(plan_id) ON DELETE RESTRICT` |
| `official_name` | `VARCHAR(150)` | `NN` |
| `trade_name` | `VARCHAR(150)` | |
| `cnpj` | `CHAR(14)` | `NN` `UQ` `CHECK fn_validate_cnpj` |
| `email` | `VARCHAR(150)` | `NN`; mascarado no formato legado ou `EMAIL_SHA256_*` |
| `phone` | `VARCHAR(80)` | mascarado no formato legado ou `PHONE_SHA256_*` |
| `latitude` / `longitude` | `DECIMAL(9,6)` | `CHECK` faixas globais |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |

**Observações:** sujeita a **RLS** (isolamento por locatário).

## `retail_store`

Unidade/filial da empresa; cada loja gerencia seu próprio estoque, também usada como **fonte/destino** de transferências e **destino** de geocercas do cliente.

| Coluna | Tipo | Restrições |
|---|---|---|
| `store_id` 🔑 | `INTEGER` identity | `PK` |
| `company_id` 🔗 | `INTEGER` | `NN` `FK → company(company_id) ON DELETE RESTRICT` |
| `address_id` 🔗 | `INTEGER` | `NN` `FK → address(address_id) ON DELETE RESTRICT` |
| `name` | `VARCHAR(120)` | `NN` |
| `cnpj` | `CHAR(14)` | `NN` `UQ` `CHECK fn_validate_cnpj` |
| `email` / `phone` | `VARCHAR` | mascarados no formato legado ou tokens SHA-256 prefixados |
| `latitude` / `longitude` | `DECIMAL(9,6)` | `CHECK` faixas globais |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | `created_at`, `updated_at`, `deleted_at` |

**Observações:** sujeita a **RLS**.

## `employee_role`

Cargo/papel do funcionário; define o **nível de permissão** (Operador de caixa, Estoquista, Gerente, Dono).

| Coluna | Tipo | Restrições |
|---|---|---|
| `role_id` 🔑 | `INTEGER` identity | `PK` |
| `name` 🔎 | `VARCHAR(80)` | `NN` `UQ` |
| `description` | `TEXT` | |
| `permission_level` ✅ | `INTEGER` | `NN` `CHECK ≥ 0` |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

## `employee`

Funcionário vinculado a uma loja e a um papel.

| Coluna | Tipo | Restrições |
|---|---|---|
| `employee_id` 🔑 | `INTEGER` identity | `PK` |
| `store_id` 🔗 | `INTEGER` | `NN` `FK → retail_store(store_id) ON DELETE RESTRICT` |
| `role_id` 🔗 | `INTEGER` | `NN` `FK → employee_role(role_id) ON DELETE RESTRICT` |
| `cpf_lookup_hmac` | `BYTEA` | HMAC-SHA-256 secreto para busca/unicidade; índice único parcial |
| `email_lookup_hmac` | `BYTEA` | HMAC-SHA-256 secreto opcional; índice único parcial |
| `hire_date` | `DATE` | `NN` `def CURRENT_DATE` |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

**Observações:** sujeita a **RLS**. Nome, CPF, e-mail e telefone não permanecem
nesta tabela depois da finalização; ficam cifrados em `employee_private_data`.

## `employee_private_data`

Cofre lógico 1:1 dos dados pessoais do funcionário, integralmente excluído da
carga analítica.

| Coluna | Tipo | Restrições |
|---|---|---|
| `employee_id` 🔑🔗 | `INTEGER` | `PK`, `FK → employee(employee_id) ON DELETE CASCADE` |
| `*_ciphertext` | `BYTEA` | Ciphertext AES-256-GCM com tag para nome, CPF, e-mail e telefone |
| `*_nonce` | `BYTEA` | 12 bytes, exclusivo por campo e cifragem |
| `*_masked` | `VARCHAR` | Apresentação segura, nunca fonte de descriptografia |
| `key_version` | `SMALLINT` | versão positiva da chave externa |
| `algorithm` | `VARCHAR(20)` | somente `AES-256-GCM` |
| `protection_state` | `VARCHAR(20)` | `MIGRATION_PENDING` ou `ENCRYPTED` |
| `encrypted_at`, `created_at`, `updated_at` | `TIMESTAMPTZ` | auditoria do envelope |

## `app_user`

Credencial de acesso de um funcionário (login e senha). Cada funcionário tem **no máximo um** usuário.

| Coluna | Tipo | Restrições |
|---|---|---|
| `user_id` 🔑 | `INTEGER` identity | `PK` |
| `employee_id` 🔗 | `INTEGER` | `NN` `UQ` `FK → employee(employee_id) ON DELETE RESTRICT` |
| `password_hash` | `VARCHAR(255)` | `NN`; BCrypt `$2a$`, `$2b$` ou `$2y$` |
| `firebase_uid` 🔎 | `VARCHAR(128)` | `UQ`; obrigatório quando a conta está ativa |
| `password_set` | `BOOLEAN` | `NN` `def TRUE`; falso durante convite inicial |
| `last_login` | `TIMESTAMP` | |
| `active` | `BOOLEAN` | `def TRUE` |
| timestamps | `TIMESTAMP` | |

**Segurança:** `app_user` não duplica CPF nem e-mail. A identidade pessoal vem
do vínculo `employee_id`; autenticação externa usa `firebase_uid`. Conta sem UID
permanece inativa como convite pendente. RLS permite o próprio usuário e a
administração autorizada da empresa. A API não envia senha original; o banco
exige BCrypt.

## `staff_session`

Sessão revogável de funcionário. Um usuário pode manter sessões distintas por dispositivo.

| Coluna | Tipo | Restrições |
|---|---|---|
| `session_id` 🔑 | `UUID` | `PK` `def gen_random_uuid()` |
| `user_id` 🔗 | `INTEGER` | `NN` `FK → app_user(user_id) ON DELETE RESTRICT` |
| `refresh_token_hash` | `TEXT` | `NN` `UQ`; SHA-256 hexadecimal de token aleatório, nunca o original |
| `refresh_expires_at` | `TIMESTAMPTZ` | `NN` posterior à criação |
| `last_used_at` / `revoked_at` | `TIMESTAMPTZ` | controles de rotação e revogação |
| `revoked_reason` | `VARCHAR(80)` | exige `revoked_at` preenchido |
| `ip_address` | `INET` | origem observada |
| `user_agent` | `VARCHAR(500)` | dispositivo cliente limitado |
| `created_at` | `TIMESTAMPTZ` | `NN` `def CURRENT_TIMESTAMP` |

**Segurança:** RLS por usuário/empresa; logout e troca de senha revogam sem excluir a evidência.

## `address`

Endereço reutilizado por empresa/loja e fornecedor. Cliente armazena apenas `address_token`, sem ligação ao endereço aberto.

| Coluna | Tipo | Restrições |
|---|---|---|
| `address_id` 🔑 | `INTEGER` identity | `PK` |
| `zip_code` ✅ | `CHAR(8)` | `NN` `CHECK ~ ^\d{8}$` |
| `street` | `VARCHAR(150)` | `NN` |
| `number` | `VARCHAR(10)` | `NN` |
| `complement` | `VARCHAR(100)` | |
| `neighborhood` | `VARCHAR(100)` | `NN` |
| `city` | `VARCHAR(100)` | `NN` |
| `state` ✅ | `CHAR(2)` | `NN` `CHECK ^[A-Z]{2}$` |
| timestamps | `TIMESTAMP` | |

---

*Próximo: [03 — Produto e Compras](03-produto-e-compras.md)*
