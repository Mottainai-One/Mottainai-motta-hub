# Guia Operacional dos Bancos Mottainai

Esta pasta reúne os procedimentos para instalar, atualizar e operar os dois
bancos PostgreSQL do ecossistema.

| Documento | Quando consultar |
|---|---|
| [01-instalar-e-atualizar.md](01-instalar-e-atualizar.md) | Instalação nova, migration e pareamento de ambiente |
| [02-api-sessoes-e-rls.md](02-api-sessoes-e-rls.md) | Implementação de login, refresh, logout e transações da API |
| [03-backup-monitoramento-e-lgpd.md](03-backup-monitoramento-e-lgpd.md) | Produção, incidentes, continuidade e privacidade |
| [04-limpeza-recarga-e-finalizacao-pii.md](04-limpeza-recarga-e-finalizacao-pii.md) | Remover dataload de teste, recarregar o legado e concluir a migração AES-GCM |

## Princípios

1. Aplicar scripts pelo `psql` com `ON_ERROR_STOP`.
2. Fazer backup e testar restauração antes de migration destrutiva.
3. Executar primeiro o operacional e depois o analítico.
4. Nunca executar `dataLoad.sql` em produção.
5. Validar as suítes SQL antes de liberar a API.
6. Manter owner/migrator separado da role utilizada pela aplicação.
