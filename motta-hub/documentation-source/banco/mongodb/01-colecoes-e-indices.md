# Coleções e índices do MongoDB

Este catálogo reproduz os campos declarados no schema da IA. **Obrigatório** significa que o validador exige o campo; campos adicionais podem existir e não são listados aqui. Tipos com `null` aceitam valor nulo, mas isso não significa que o campo seja obrigatório.

As configurações `strict` e `error` abaixo são as declaradas no repositório; confirme a aplicação na instância com `python scripts/setup_mongo.py --check` no projeto da IA. Índices não são chaves estrangeiras: integridade entre documentos depende da aplicação.

## `agent_contexts`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `agent` | string | Sim |
| `currentSkill` | string / null | Não |
| `state` | object | Não |
| `createdAt` | date | Sim |
| `updatedAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_agent_contexts_updatedAt` | `updatedAt: -1` | Não |
| `ux_agent_contexts_conversation_agent` | `conversationId: 1`, `agent: 1` | Sim |

## `agent_executions`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId / null | Não |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `tools` | array / null de string | Não |
| `executionFlow` | array / null de string | Não |
| `status` | enum: running, completed, error | Sim |
| `latency` | double / null | Não |
| `startedAt` | date | Sim |
| `finishedAt` | date / null | Não |
| `error` | object / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `agent_1_status_1` | `agent: 1`, `status: 1` | Não |
| `empresaId_1_createdAt_-1` | `empresaId: 1`, `createdAt: -1` | Não |
| `ix_agent_executions_agent_status_startedAt` | `agent: 1`, `status: 1`, `startedAt: -1` | Não |
| `ix_agent_executions_conversation_startedAt` | `conversationId: 1`, `startedAt: -1` | Não |

## `agent_fallbacks`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `sourceAgent` | string | Sim |
| `fallbackAgent` | string | Sim |
| `reason` | string | Sim |
| `active` | bool | Sim |
| `createdAt` | date | Sim |
| `updatedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ux_agent_fallbacks_source_fallback` | `sourceAgent: 1`, `fallbackAgent: 1` | Sim |

## `agent_policies`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `agent` | string | Sim |
| `scope` | object | Sim |
| `canUseRag` | bool / null | Não |
| `canUseTools` | bool / null | Não |
| `canReadMemory` | bool / null | Não |
| `canWriteMemory` | bool / null | Não |
| `active` | bool | Sim |
| `createdAt` | date | Sim |
| `updatedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ux_agent_policies_agent` | `agent: 1` | Sim |

## `ai_results`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `type` | enum: recommendation, prediction, analysis, summary | Sim |
| `result` | object | Sim |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_ai_results_agent_type_createdAt` | `agent: 1`, `type: 1`, `createdAt: -1` | Não |
| `ix_ai_results_conversation_createdAt` | `conversationId: 1`, `createdAt: -1` | Não |

## `cache_queries`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `queryHash` | string | Sim |
| `response` | string | Sim |
| `expiresAt` | date | Sim |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_cache_queries_expiresAt` | `expiresAt: 1` | Não |
| `ux_cache_queries_queryHash` | `queryHash: 1` | Sim |

## `conversation_events`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `type` | enum: conversation_started, intent_detected, agent_selected, tool_called, fallback_used, response_sent, conversation_closed, error | Sim |
| `payload` | object / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_conversation_events_conversation_createdAt` | `conversationId: 1`, `createdAt: 1` | Não |
| `ix_conversation_events_type_createdAt` | `type: 1`, `createdAt: -1` | Não |

## `conversations`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `sessionId` | string | Sim |
| `empresaId` | int | Sim |
| `usuarioId` | int | Sim |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `status` | string | Sim |
| `title` | string / null | Não |
| `startedAt` | date | Sim |
| `lastInteraction` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `empresaId_1_status_1` | `empresaId: 1`, `status: 1` | Não |
| `ix_conversations_empresa_usuario_lastInteraction` | `empresaId: 1`, `usuarioId: 1`, `lastInteraction: -1` | Não |
| `ix_conversations_agent_status` | `agent: 1`, `status: 1` | Não |
| `ix_conversations_empresa_usuario_startedAt` | `empresaId: 1`, `usuarioId: 1`, `startedAt: -1` | Não |
| `ix_conversations_lastInteraction` | `lastInteraction: -1` | Não |
| `ux_conversations_sessionId` | `sessionId: 1` | Sim |

## `embeddings_cache`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `hash` | string | Sim |
| `embedding` | array de double | Sim |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ux_embeddings_cache_hash` | `hash: 1` | Sim |

## `feedbacks`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `messageId` | objectId | Sim |
| `usuarioId` | int | Sim |
| `agent` | string / null | Não |
| `rating` | enum: positive, negative, neutral | Sim |
| `comment` | string / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_feedbacks_messageId` | `messageId: 1` | Não |
| `ix_feedbacks_usuario_createdAt` | `usuarioId: 1`, `createdAt: -1` | Não |

## `intent_catalog`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `key` | string | Sim |
| `label` | string | Não |
| `description` | string / null | Não |
| `agent` | string | Sim |
| `skill` | string | Não |
| `examples` | array / null de string | Não |
| `confidenceThreshold` | double / null | Não |
| `active` | bool | Sim |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_intent_catalog_agent_active` | `agent: 1`, `active: 1` | Não |
| `ix_intent_catalog_skill` | `skill: 1` | Não |
| `ux_intent_catalog_key` | `key: 1` | Sim |

## `memories`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `usuarioId` | int | Sim |
| `empresaId` | int | Sim |
| `preferences` | array / null de string | Não |
| `facts` | array / null de string | Não |
| `lastAgent` | string / null | Não |
| `lastSkill` | string / null | Não |
| `updatedAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_memories_updatedAt` | `updatedAt: -1` | Não |
| `ux_memories_empresa_usuario` | `empresaId: 1`, `usuarioId: 1` | Sim |

## `messages`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `role` | enum: user, assistant, system, tool | Sim |
| `content` | string | Sim |
| `agent` | string / null | Não |
| `skill` | string / null | Não |
| `model` | string / null | Não |
| `sources` | array / null de object | Não |
| `inputTokens` | int / long / null | Não |
| `outputTokens` | int / long / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_messages_agent_skill_createdAt` | `agent: 1`, `skill: 1`, `createdAt: -1` | Não |
| `ix_messages_conversation_createdAt` | `conversationId: 1`, `createdAt: 1` | Não |

## `metrics`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId / null | Não |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `model` | string / null | Não |
| `inputTokens` | int / long / null | Não |
| `outputTokens` | int / long / null | Não |
| `latency` | double / null | Não |
| `estimatedCost` | double / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `agent_1_createdAt_-1` | `agent: 1`, `createdAt: -1` | Não |
| `createdAt_-1` | `createdAt: -1` | Não |
| `ix_metrics_empresa_createdAt` | `empresaId: 1`, `createdAt: -1` | Não |
| `ix_metrics_agent_skill_createdAt` | `agent: 1`, `skill: 1`, `createdAt: -1` | Não |
| `ix_metrics_conversation_createdAt` | `conversationId: 1`, `createdAt: -1` | Não |

## `prompt_evaluations`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `promptVersion` | string | Sim |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `score` | double | Sim |
| `feedback` | string / null | Não |
| `evaluator` | string / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_prompt_evaluations_empresa_createdAt` | `empresaId: 1`, `createdAt: -1` | Não |
| `ix_prompt_evaluations_createdAt` | `createdAt: -1` | Não |
| `ix_prompt_evaluations_prompt_agent` | `promptVersion: 1`, `agent: 1` | Não |

## `prompts`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `version` | string | Sim |
| `systemPrompt` | string | Sim |
| `temperature` | double / null | Não |
| `model` | string | Sim |
| `active` | bool | Sim |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_prompts_agent_skill_active` | `agent: 1`, `skill: 1`, `active: 1` | Não |
| `ux_prompts_agent_skill_version` | `agent: 1`, `skill: 1`, `version: 1` | Sim |

## `rag_chunks`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `documentId` | objectId | Sim |
| `chunk` | int | Sim |
| `text` | string | Sim |
| `embedding` | array / null de double | Não |
| `metadata` | object / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `documentId_1` | `documentId: 1` | Não |
| `documentId_1_chunk_1` | `documentId: 1`, `chunk: 1` | Não |
| `ux_rag_chunks_document_chunk` | `documentId: 1`, `chunk: 1` | Sim |

## `rag_documents`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `empresaId` | int | Sim |
| `title` | string | Sim |
| `category` | enum: MANUAL, FAQ, PROCEDIMENTO, TREINAMENTO, POLITICA | Sim |
| `version` | string | Sim |
| `metadata` | object / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `empresaId_1` | `empresaId: 1` | Não |
| `ux_rag_documents_empresa_slug` | `empresaId: 1`, `slug: 1` | Sim |
| `ix_rag_documents_empresa_category_createdAt` | `empresaId: 1`, `category: 1`, `createdAt: -1` | Não |
| `tx_rag_documents_title` | `title: text` | Não |
| `ux_rag_documents_empresa_title_version` | `empresaId: 1`, `title: 1`, `version: 1` | Sim |

## `response_explanations`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `messageId` | objectId | Sim |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `explanation` | string | Sim |
| `sources` | array / null de string | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_response_explanations_agent_createdAt` | `agent: 1`, `createdAt: -1` | Não |
| `ux_response_explanations_messageId` | `messageId: 1` | Sim |

## `routing_logs`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `intent` | string | Sim |
| `selectedAgent` | string | Sim |
| `selectedSkill` | string / null | Não |
| `confidence` | double / null | Não |
| `createdAt` | date | Sim |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_routing_logs_conversation_createdAt` | `conversationId: 1`, `createdAt: -1` | Não |
| `ix_routing_logs_intent_createdAt` | `intent: 1`, `createdAt: -1` | Não |

## `skill_executions`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `empresaId` | int | Sim |
| `usuarioId` | int | Sim |
| `sessionId` | string | Sim |
| `conversationId` | objectId / null | Não |
| `skill` | string | Sim |
| `version` | string | Sim |
| `status` | enum: success, denied, invalid_input, invalid_output, error, timeout | Sim |
| `input` | object / null | Não |
| `output` | object / null | Não |
| `error` | object / null | Não |
| `latency` | double / null | Não |
| `startedAt` | date | Sim |
| `finishedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_skill_executions_empresa_skill_startedAt` | `empresaId: 1`, `skill: 1`, `startedAt: -1` | Não |
| `ix_skill_executions_status` | `status: 1` | Não |

## `skill_registry`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `empresaId` | int | Sim |
| `name` | string | Sim |
| `version` | string | Sim |
| `description` | string | Sim |
| `owner` | string | Sim |
| `entrypoint` | string | Sim |
| `timeoutSeconds` | double | Sim |
| `maxRetries` | int / null | Não |
| `scope` | enum: read_only, write_with_approval | Sim |
| `requiredRoles` | array de string | Sim |
| `inputSchema` | object | Sim |
| `outputSchema` | object | Sim |
| `tags` | array / null de string | Não |
| `active` | bool | Sim |
| `createdAt` | date | Sim |
| `updatedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ux_skill_registry_empresa_name_version` | `empresaId: 1`, `name: 1`, `version: 1` | Sim |
| `ix_skill_registry_empresa_active` | `empresaId: 1`, `active: 1` | Não |

## `tool_permissions`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `agent` | string | Sim |
| `tool` | string | Sim |
| `action` | string / null | Não |
| `canExecute` | bool | Não |
| `canRead` | bool | Não |
| `active` | bool | Sim |
| `createdAt` | date | Sim |
| `updatedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ux_tool_permissions_agent_tool` | `agent: 1`, `tool: 1` | Sim |

## `tool_runs`

Validação declarada: `strict` / `error`.

| Campo | Tipo ou valores declarados | Obrigatório |
|---|---|---|
| `_id` | objectId | Não |
| `conversationId` | objectId | Sim |
| `agent` | string | Sim |
| `skill` | string / null | Não |
| `tool` | string | Sim |
| `input` | object / null | Não |
| `output` | object / null | Não |
| `status` | enum: running, success, error | Sim |
| `latency` | double / null | Não |
| `error` | object / null | Não |
| `startedAt` | date | Sim |
| `finishedAt` | date / null | Não |

| Índice declarado | Chaves (ordem) | Único |
|---|---|---|
| `ix_tool_runs_agent_tool_startedAt` | `agent: 1`, `tool: 1`, `startedAt: -1` | Não |
| `ix_tool_runs_conversation_startedAt` | `conversationId: 1`, `startedAt: -1` | Não |
| `ix_tool_runs_status` | `status: 1` | Não |
