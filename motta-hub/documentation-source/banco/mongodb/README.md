# MongoDB da camada de IA

O MongoDB guarda conversas, mensagens, memória, execução de agentes, métricas,
conteúdo de RAG e configurações da IA. A API Mongo oferece consultas e curadoria
de parte dessas coleções; a IA também acessa o banco diretamente. O PostgreSQL
continua responsável pelos dados transacionais descritos no [índice de bancos](../README.md).

## Leitura recomendada

1. [Coleções, campos e índices](01-colecoes-e-indices.md)
2. [API, integração e operação](02-api-integracao-e-operacao.md)
3. [Contratos e endpoints da API MongoDB](../../api/mongodb/README.md)

O catálogo reflete o schema versionado no commit `021fdc0` da IA e a API no
commit `8b3544e`. Ele descreve o contrato versionado, não comprova a configuração
ou os dados presentes em uma instância em execução. A referência executável de
schema e índices é [`scripts/mongo/schema.json`](https://github.com/Mottainai-One/Mottainai-IA/blob/021fdc0/scripts/mongo/schema.json).
