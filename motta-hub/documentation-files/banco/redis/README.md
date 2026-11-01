# Redis: notificações e usos pela IA

O Redis atende a caixa de notificações consumida pelo aplicativo e também
contém chaves usadas pela IA. A [API Redis](https://github.com/Mottainai-One/Mottainai-Redis-Api/tree/8631908)
consome eventos de um Stream e expõe a caixa via HTTP. A IA acessa Redis
diretamente para outras funções. A topologia e a política de memória da
instância real dependem da implantação.

## Leitura recomendada

1. [Estruturas e fluxo de notificações](01-estruturas-e-notificacoes.md)
2. [API, segurança e operação](02-api-seguranca-e-operacao.md)
3. [Contratos e endpoints da API Redis](../../api/redis/README.md)

Referências: API no commit `8631908` e IA no commit `021fdc0`. Esta documentação
descreve código versionado, não comprova configuração em produção. Voltar ao
[índice de bancos](../README.md).
