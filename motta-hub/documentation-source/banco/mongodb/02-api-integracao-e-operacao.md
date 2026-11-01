# MongoDB: API, integração e operação

## Relações e responsabilidade

- `conversations` identifica a sessão e a empresa; `messages`, `agent_executions` e outras coleções podem referenciar a conversa por `conversationId`.
- `rag_documents` pertence a uma empresa; `rag_chunks.documentId` aponta para o documento. A API verifica o documento pai para aplicar o escopo aos chunks.
- `memories` associa empresa e usuário. `metrics` e execuções fornecem observabilidade; o `requestId`, quando presente, ajuda a correlacionar registros. Registros antigos podem não conter esse campo.
- O schema contém ainda catálogos, políticas, execuções de ferramentas, cache de embeddings, avaliações e outras coleções; veja o [catálogo completo](01-colecoes-e-indices.md).

## API Mongo

O prefixo é `/api/v1`. A tabela resume os controllers da [API Mongo](https://github.com/Mottainai-One/Mottainai-Api-NoSQL/tree/8b3544e/src/main/java/com/mottainai/mongoapi/controller):

| Recurso | Operações |
|---|---|
| `/conversations` | Listar, consultar por `sessionId` e listar mensagens da sessão. |
| `/metrics`, `/metrics/summary` | Consultar métricas e resumo. |
| `/executions` | Consultar execuções de agentes. |
| `/memories` | Listar, consultar e excluir memória por empresa e usuário. |
| `/rag/documents` | Listar, consultar, criar, editar e excluir documentos; listar e criar chunks. |
| `/rag/chunks/{id}` | Editar e excluir chunk. |
| `/rag/search` | Buscar documentos por texto. |

O escopo de empresa é fornecido em parâmetro, caminho ou corpo conforme a rota;
consulte os controllers e DTOs para os campos exatos. A busca por recursos de
outra empresa retorna 404 onde o recurso é verificado. **O `empresaId` fornecido
pelo chamador não é, por si só, autenticação nem prova de autorização**: a versão
inspecionada não declara Spring Security no projeto. Proteja a API em uma camada
autenticada e valide o vínculo do usuário com a empresa antes de expô-la.

O resumo de métricas calcula `errorRate` como proporção entre 0 e 1; ausência de
nota do Judge não equivale a reprovação. `avgLatency` pode ser omitida quando
não há latências no grupo. Valores calculados da resposta não devem ser tratados
automaticamente como campos persistidos.

## RAG e embeddings

O upload de `POST /rag/documents` da **IA** cria chunks e embeddings. A API Java
mantém documentos e chunks, mas chunks criados por ela não recebem embeddings.
Ao alterar o texto, a API invalida o embedding anterior; mudanças apenas de
número ou metadata o preservam. Para processar vetores pendentes, use o fluxo
da IA (`python scripts/generate_embeddings.py`) conforme a configuração do
ambiente. O cache de RAG pode conservar uma resposta anterior até expirar;
o padrão documentado na IA é 300 segundos. A disponibilidade de busca vetorial
e do modelo depende do ambiente e não foi validada aqui.

## Operação

1. Configure a conexão por variáveis do ambiente da IA e da API; nunca registre URI com senha em documentação ou logs compartilhados.
2. No repositório da IA, `python scripts/setup_mongo.py --check` compara o banco com o schema declarado e retorna erro em divergências. O check não prova que não existam coleções ou índices adicionais.
3. `python scripts/setup_mongo.py` altera coleções, validadores, índices e sincroniza o catálogo de intenções. Execute somente após revisar impacto, permissões e backup; `--seed-demo` adiciona dados de demonstração.
4. Monitore conectividade, falhas de validação, índices e tamanho. Faça backup e teste restauração em ambiente isolado, seguindo a política da implantação; não há evidência aqui de backup configurado.

**Limites da análise:** o estado de MongoDB em execução, os índices efetivos,
acessos, backups e integração ponta a ponta não foram inspecionados. A fonte de
verdade para validadores e índices é o schema versionado da IA, não o Hub.
