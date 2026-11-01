# API MongoDB

> Contrato inspecionado em 31/10/2026: [Mottainai-Api-NoSQL, commit `8b3544e`](https://github.com/Mottainai-One/Mottainai-Api-NoSQL/tree/8b3544e). Os exemplos são ilustrativos e não comprovam uma implantação em execução.

A API Java/Spring expõe dados da camada de IA armazenados no MongoDB. Ela permite consultar conversas, mensagens, métricas e execuções, consultar ou excluir memórias e manter documentos e trechos da base de conhecimento RAG. O modelo de dados e os índices estão no [guia do banco MongoDB](../../banco/mongodb/README.md).

## Endereço, configuração e segurança

- Prefixo das rotas: `/api/v1`. A porta padrão do processo é `8080`, configurável por `SERVER_PORT`.
- `SPRING_DATA_MONGODB_URI` configura a conexão; o padrão local do código é `mongodb://localhost:27017/mottainai`. Não compartilhe URIs com credenciais.
- O Swagger UI está configurado em `/swagger-ui.html` e o documento OpenAPI em `/v3/api-docs`.
- O escopo `empresaId` é recebido no parâmetro, caminho ou corpo conforme a operação. A consulta filtra a empresa, mas **o ID informado pelo cliente não autentica nem autoriza o usuário**. A versão inspecionada não declara Spring Security; antes de expor a API, uma camada confiável deve autenticar o chamador e validar seu vínculo com a empresa.
- A API não cria índices automaticamente. O schema e os índices são mantidos pela camada de IA; instalação e verificação estão no [guia de operação do MongoDB](../../banco/mongodb/02-api-integracao-e-operacao.md).

As listas retornam objetos `Page` do Spring Data. Os parâmetros de paginação são `page`, `size` e `sort`; o tamanho padrão configurado é 20 e o máximo é 100. A ordenação padrão depende da rota, conforme abaixo. Datas `Instant`, quando aceitas em filtros, devem ser enviadas em formato ISO 8601, por exemplo `2026-10-01T00:00:00Z`. Valores nulos são omitidos das respostas pela configuração Jackson.

## Conversas e mensagens

Todas as rotas desta seção usam `GET` e exigem `empresaId` na query.

| Rota | Parâmetros adicionais | Resultado |
|---|---|---|
| `/api/v1/conversations` | `usuarioId`, `status`, paginação; ordenação padrão `startedAt` | Página de conversas da empresa. |
| `/api/v1/conversations/{sessionId}` | — | Uma conversa da sessão. |
| `/api/v1/conversations/{sessionId}/messages` | Paginação; ordenação padrão `createdAt` | Página de mensagens da conversa. |

Uma conversa pode retornar `sessionId`, `empresaId`, `usuarioId`, `agent`, `skill`, `status`, `title`, `startedAt`, `lastInteraction` e `endedAt`. Uma mensagem pode conter `id`, `requestId`, `conversationId`, `role`, `content`, `agent`, `skill`, `model`, `sources`, `inputTokens`, `outputTokens` e `createdAt`. Campos opcionais ou ausentes não devem ser presumidos. A API não cria nem edita conversas ou mensagens.

```http
GET /api/v1/conversations?empresaId=1&usuarioId=10&page=0&size=20
```

## Métricas e execuções

Todas as rotas usam `GET` e exigem `empresaId` na query.

| Rota | Filtros adicionais | Resultado |
|---|---|---|
| `/api/v1/metrics` | `agent`, `from`, `to`, paginação; ordenação padrão `createdAt` | Página de métricas. |
| `/api/v1/metrics/summary` | `from`, `to` | Agregação por agente. |
| `/api/v1/executions` | `agent`, `status`, paginação; ordenação padrão `createdAt` | Página de execuções. |

O resumo retorna `empresaId`, `from`, `to` e `agents`. Cada item de `agents` contém `agent`, `totalExecutions`, `totalCost`, `avgLatency`, `avgJudgeScore` e `errorRate`, sujeitos à omissão de nulos. A taxa de erro é proporção de 0 a 1: considera status diferente de `completed` ou nota do Judge inferior a 0,7, contando cada execução uma vez; nota ausente não é reprovação. Sem latências no grupo, `avgLatency` é omitida. `requestId` pode correlacionar mensagens, métricas e execuções, mas pode não existir em dados antigos.

## Memórias

| Método e rota | Parâmetros | Resultado |
|---|---|---|
| `GET /api/v1/memories` | Query `empresaId`; paginação, padrão de ordenação `usuarioId` | Página de memórias. |
| `GET /api/v1/memories/{empresaId}/{usuarioId}` | IDs no caminho | Memória do usuário na empresa. |
| `DELETE /api/v1/memories/{empresaId}/{usuarioId}` | IDs no caminho | Exclui a memória e retorna `204` sem corpo. |

Uma memória pode conter `empresaId`, `usuarioId`, `preferences`, `facts`, `lastAgent`, `lastSkill` e `updatedAt`. Não existem rotas para criar ou editar memória nesta API.

## Documentos RAG

| Método e rota | Escopo e filtros | Resultado |
|---|---|---|
| `GET /api/v1/rag/documents` | Query `empresaId`; filtros opcionais `source`, `category`, paginação; ordem padrão `createdAt` | Página de documentos. Se ambos os filtros vierem preenchidos, `category` tem precedência. |
| `GET /api/v1/rag/documents/{id}` | Query `empresaId` | Documento pelo ID. |
| `GET /api/v1/rag/documents/slug/{slug}` | Query `empresaId` | Documento pelo slug. |
| `POST /api/v1/rag/documents` | `empresaId` no corpo | Cria e retorna o documento com `201`. |
| `PUT /api/v1/rag/documents/{id}` | Query `empresaId` e corpo validado | Atualiza o documento; não altera a empresa proprietária. |
| `DELETE /api/v1/rag/documents/{id}` | Query `empresaId` | Exclui o documento e seus chunks; retorna `204`. |
| `GET /api/v1/rag/search` | Query `empresaId`, `q` e paginação | Busca textual em títulos de documentos da empresa. Não é busca semântica. |

O corpo de criação e atualização usa estes campos:

| Campo | Regra |
|---|---|
| `empresaId` | Obrigatório, inteiro positivo até 2.147.483.647. No `PUT`, o corpo ainda é validado, mas a propriedade do documento é determinada pelo ID da query e não muda. |
| `title` | Obrigatório, não vazio, até 200 caracteres. |
| `slug` | Opcional, até 150 caracteres; letras minúsculas, números e hífens entre segmentos. O índice único também limita a um documento sem slug por empresa. |
| `source` | Opcional, até 100 caracteres; campo legado. |
| `category` | Opcional: `MANUAL`, `FAQ`, `PROCEDIMENTO`, `TREINAMENTO` ou `POLITICA`; se omitida, é derivada de `source`, com `MANUAL` como padrão. |
| `version` | Opcional, até 50 caracteres; padrão `1.0` quando ausente ou vazia. |
| `metadata` | Objeto opcional. |

Há unicidade por empresa/slug e por empresa/título/versão; duplicações retornam `409`. Exemplo de criação, com dados fictícios:

```http
POST /api/v1/rag/documents
Content-Type: application/json

{
  "empresaId": 1,
  "slug": "manual-estoque",
  "title": "Manual de estoque",
  "category": "MANUAL",
  "version": "1.0",
  "metadata": {"idioma": "pt-BR"}
}
```

A resposta de documento pode conter `id`, `slug`, `empresaId`, `title`, `source`, `category`, `version`, `metadata` e `createdAt`.

## Chunks RAG

Todas as rotas exigem `empresaId` na query e verificam o documento proprietário.

| Método e rota | Resultado |
|---|---|
| `GET /api/v1/rag/documents/{id}/chunks` | Página de chunks por número crescente; aceita paginação. |
| `POST /api/v1/rag/documents/{id}/chunks` | Cria um chunk e retorna `201`. |
| `PUT /api/v1/rag/chunks/{id}` | Atualiza texto e, opcionalmente, número e metadata. |
| `DELETE /api/v1/rag/chunks/{id}` | Exclui o chunk e retorna `204`. |

O corpo de `POST` e `PUT` exige `text` não vazio, com até 8.000 caracteres. `chunk` é inteiro não negativo e opcional; na criação, sua ausência usa o maior número atual mais um, ou zero. `metadata` é um objeto opcional. A resposta pode conter `id`, `documentId`, `chunk`, `text`, `metadata` e `createdAt`.

```http
POST /api/v1/rag/documents/64a000000000000000000001/chunks?empresaId=1
Content-Type: application/json

{"chunk": 0, "text": "Confira a validade dos produtos.", "metadata": {"pagina": 1}}
```

A API Java não recebe nem gera embeddings. Chunks novos ficam fora da recuperação semântica até serem processados pela IA; editar o texto invalida o vetor anterior. Para upload e geração de vetores, consulte o [fluxo RAG da IA](../../banco/mongodb/02-api-integracao-e-operacao.md#rag-e-embeddings).

## Erros e validação

O tratamento global retorna JSON com `timestamp`, `status`, `error`, `message` e `path` para exceções tratadas. Casos previstos incluem `400` para parâmetros ausentes ou inválidos e falhas de validação, `404` para recurso não encontrado no escopo, `409` para duplicação e `500` para erro não tratado. Mensagens e detalhes dependem da falha; não use a resposta como prova de autenticação.

O repositório da API contém testes unitários e de integração com MongoDB via Testcontainers; consulte o `pom.xml` e a configuração de testes antes de executar `mvn verify`. Esta documentação foi conferida contra o código e os DTOs, sem chamadas HTTP à implantação ou teste ponta a ponta.
