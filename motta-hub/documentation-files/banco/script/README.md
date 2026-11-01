# Scripts SQL do Banco Operacional

> Fonte executável: repositório `Mottainai-Banco-Operacional`

Os scripts atuais ficam em `database/operational`. A pasta legada `script/`
permanece apenas para compatibilidade de testes antigos e não é a referência de
uma instalação nova.

## Instalação

```bash
psql -v ON_ERROR_STOP=1 \
  -d mottainai_operational \
  -f database/operational/install.sql
```

O instalador usa `\ir` e abre uma transação única com interrupção no primeiro
erro. Ele não apaga schema, banco ou dados existentes.

## Módulos

| Ordem | Arquivo | Responsabilidade |
|---|---|---|
| 1 | `00_database.sql` | Extensões, schema e `search_path` |
| 2 | `01_enums.sql` | Estados do domínio |
| 3 | `02_functions.sql` | Validação, estoque, FEFO, custo e eventos |
| 4 | `03_tables.sql` | Estrutura operacional principal |
| 5 | `04_additional_tables.sql` | CPF da conta, preços por loja, inventário físico, tokens e outbox |
| 6 | `04_security.sql` | Políticas RLS básicas |
| 7 | `05_indexes.sql` | Índices de busca e apoio a FKs |
| 8 | `06_triggers.sql` | SKU, lote, FEFO, histórico e auditoria |
| 9 | `07_views.sql` | Views operacionais |
| 10 | `08_procedures.sql` | Partições e regras transacionais |
| 11 | `08_partition_maintenance_fix.sql` | Correção segura de manutenção mensal |
| 12 | `09_seed.sql` | Catálogos mínimos e versão inicial |
| 13 | `10_product_company.sql` | Propriedade de produto por empresa |
| 14 | `10_tests.sql` | Validações estruturais gerais |
| 15 | `11_product_company_tests.sql` | Testes da migration de produto |
| 16 | `20_security_hardening.sql` | Roles, sessões, RLS, auditoria e privilégios |
| 17 | `21_security_hardening_tests.sql` | Testes automatizados de segurança |
| 18 | `22_sensitive_data_contract.sql` | Contrato SHA-256/BCrypt, proteção de clientes, RPA e RLS dedicado |
| 19 | `23_sensitive_data_contract_tests.sql` | Testes do contrato de dados sensíveis |
| 20 | `24_jpa_compatibility.sql` | Compatibilidade aditiva de usuários e recuperação de senha |
| 21 | `25_api_rpa_compatibility.sql` | Contrato de views/funções da API e contexto seguro da RPA |
| 22 | `26_api_rpa_compatibility_tests.sql` | Testes estruturais, idempotência, auditoria, pedido e recebimento |
| 23 | `27_protected_reinstall_fixture.sql` | Fixture segura para validar reaplicação sobre dados protegidos |
| 24 | `28_reversible_employee_pii.sql` | Envelope AES-256-GCM para dados recuperáveis de funcionários |
| 25 | `29_finalize_reversible_employee_pii.sql` | Contrato final de identidade protegida de funcionários |
| 26 | `30_customer_private_data.sql` | Estrutura inicial do envelope privado de clientes |
| 27–32 | `31_...sql` a `36_...sql` | Contrato incremental do PDV, idempotência, cliente e soft delete de promoções |
| 33 | `37_reversible_customer_pii.sql` | Envelope final, exclusão lógica e acesso interno autorizado |
| 34 | `38_client_mobile_api.sql` | Roles, views e funções isoladas do backend mobile |

## Garantias relevantes

- migrations novas são idempotentes;
- dados antigos são preenchidos antes de `NOT NULL`;
- propriedade ambígua de produto interrompe a migration;
- role da API não é criada com login ou senha;
- testes verificam privilégios, RLS, views e auditoria;
- dados pessoais abertos são recusados e logs são sanitizados recursivamente;
- CI instala o schema em PostgreSQL 15 limpo e reaplica migrations críticas.

Para atualizar uma base já instalada, execute
`update_existing_api_rpa.sql`. O agregador aplica, em uma transação, os
módulos de produto, segurança, dados sensíveis, JPA e compatibilidade API/RPA.

Para aplicar somente o contrato final de cliente/mobile sobre uma base já
atualizada, execute `update_existing_customer_private_data.sql`.

Veja [01-estrutura-do-script.md](01-estrutura-do-script.md) e o
[guia de instalação](../operacao/01-instalar-e-atualizar.md).
