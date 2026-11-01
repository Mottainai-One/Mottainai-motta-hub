# Redis: API, segurança e operação

## API de notificações

| Método e rota | Comportamento |
|---|---|
| `GET /livez` | Processo vivo; não consulta Redis. |
| `GET /readyz` | Verifica acesso ao Redis. |
| `GET /v1/notifications?limit=20` | Lista a caixa e o total não lido; limite entre 1 e 100. |
| `POST /v1/notifications/{id}/read` | Marca como lida de forma idempotente; retorna 404 se não encontrada. |

A API não possui rota HTTP para criar notificações. As rotas de notificações
exigem JWT Bearer HS256, com `exp`, `sub`, `empresa_id` e `role`. Os perfis
aceitos são `CLIENTE`, `ESTOQUISTA`, `GERENTE` e `DONO`; empresa e usuário
vêm do token. O segredo deve ter ao menos 32 caracteres. A configuração usa
`REDIS_URL` e `JWT_SECRET`, além de `NOTIFICATION_STREAM_KEY`,
`NOTIFICATION_STREAM_GROUP` e `NOTIFICATION_STREAM_RECLAIM_IDLE_MS` opcionais.
Proteja credenciais e restrinja o acesso à rede do Redis aos serviços autorizados.

## Persistência, memória e retenção

O compose da API conecta a um Redis provisionado separadamente. Seu README
registra um ambiente observado com AOF, `maxmemory 256mb` e `volatile-lru`;
isso não comprova a configuração de qualquer outro ambiente. `volatile-lru`
pode remover chaves com TTL antes do prazo em pressão de memória. O Stream não
recebe TTL nem compactação automática pela API, portanto monitore crescimento,
consumidores e mensagens pendentes. Uma política de retenção precisa preservar
mensagens ainda necessárias; não execute `XTRIM`, `XDEL` ou limpeza genérica
sem conhecer os grupos e efeitos de perda.

Monitore disponibilidade, memória, evictions, tamanho do Stream, atrasos e
pendências do grupo. Investigue falhas persistentes antes de remover locks ou
chaves. AOF não substitui um backup testado; a estratégia de restauração deve
ser definida para a implantação. Dados de notificações podem conter informações
sensíveis: evite copiar payloads para logs ou tickets.

## Verificação

No repositório da API, `mvn verify` executa a suíte configurada. Os testes de
integração requerem Redis exclusivo de testes e `REDIS_TEST_HOST` (porta opcional
`REDIS_TEST_PORT`). Não aponte testes para uma instância produtiva. Consulte
`/readyz` para conectividade, mas esse endpoint não valida a entrega completa
de notificações nem a retenção do Stream.

**Limites da análise:** não foram consultadas a instância Redis real, suas
políticas de memória, sua persistência efetiva ou uma entrega ponta a ponta.
