# Limpeza, Recarga e Finalização de Dados Pessoais

## Escopo

Este procedimento remove exclusivamente dados de teste do banco operacional,
recarrega a fonte legada e conclui a retirada das colunas pessoais transitórias.
O banco legado permanece somente leitura e não é limpo por este processo.

## Ordem obrigatória

1. Fazer backup do operacional e validar a restauração.
2. Pausar a agenda legado → operacional e a carga analítica das 02:00.
3. Executar o script local de limpeza validado, conectado ao banco `MOTTAINAI`.
4. Confirmar que tabelas de configuração e `schema_version` foram preservadas.
5. Configurar no secret manager as chaves AES e HMAC da RPA.
6. Executar `run_migration.py` primeiro com `MIGRATION_DRY_RUN=true`.
7. Revisar quarentena e contagens; executar novamente com `false`.
8. Confirmar que todos os funcionários estão `ENCRYPTED` e que nenhuma conta
   ativa está sem `firebase_uid`.
9. Aplicar a finalização PII para remover as colunas legadas.
10. Reativar a sincronização a cada 30 minutos e a carga analítica das 02:00.

## O que a limpeza preserva

- schemas, tabelas, funções, views, policies, triggers e partições;
- roles e privilégios;
- `schema_version`, `subscription_plan`, `employee_role`, `tax_profile`,
  `system_rule`;
- contrato físico dos bancos operacional e analítico.

Todos os cadastros, transações, usuários, clientes, envelopes, logs, filas,
auditoria e registros de integração de teste são removidos. As identities das
tabelas limpas são reiniciadas.

`api_customer_transaction_context` pertence a uma role técnica. A limpeza
concede `TRUNCATE` ao migrator somente durante a transação e restaura o estado
anterior antes do `COMMIT`.

## Contrato da nova carga

A RPA lê novamente todas as tabelas legadas e faz upsert; não existe checkpoint
externo a ser apagado. Nome, CPF, e-mail e telefone de funcionário são cifrados
com AES-256-GCM antes da persistência. CPF e e-mail recebem HMACs de busca. As
chaves nunca entram no PostgreSQL, GitHub, logs ou arquivos de quarentena.

Sem `firebase_uid` real, `app_user` é criado inativo. Não é permitido inventar
UID nem marcar manualmente um envelope como `ENCRYPTED`.

## Critérios de liberação

- zero funcionários em `MIGRATION_PENDING`;
- zero funcionários sem envelope de nome/CPF, versão de chave ou data;
- zero usuários ativos sem `firebase_uid`;
- zero órfãos entre empresa, loja, funcionário e usuário;
- execução da RPA sem quarentena inesperada;
- finalização PII confirmada em uma única transação;
- smoke tests das APIs e RLS aprovados antes de reativar as agendas.
