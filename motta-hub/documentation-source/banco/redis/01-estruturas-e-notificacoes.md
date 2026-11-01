# Redis: estruturas e notificações

## Fluxo

```text
Produtor autorizado -> Redis Stream -> consumer group da API Redis
                   -> hash da notificação + inbox + contador
Aplicativo -> API Redis autenticada -> leitura e marcação como lida
```

O Stream padrão é `mottainai:v1:notification:stream` e o grupo padrão é
`notification-writers`. Ambos podem ser configurados. O consumidor cria o grupo
e o Stream se necessário, consulta até 100 registros por ciclo de um segundo e
recupera pendentes via `XPENDING` e `XCLAIM`; a espera mínima padrão é 60.000 ms.

## Contrato de entrada do Stream

| Campo | Regra |
|---|---|
| `company_id`, `user_id` | Obrigatórios; inteiros positivos. |
| `title` | Obrigatório, não vazio, até 120 caracteres. |
| `body` | Obrigatório, não vazio, até 1000 caracteres. |
| `priority` | Obrigatório: 1, 2 ou 3. |
| `id` | Opcional; até 128 caracteres e sem `:`. Ausente ou vazio gera `stream-<id-do-registro>`. |

O consumidor grava os dados e confirma com `XACK`. Mensagens inválidas são
registradas em log e confirmadas sem gravação; nesta versão não há uma dead
letter queue implementada. Falhas de gravação ou confirmação deixam a entrega
pendente para nova tentativa. A confirmação não apaga a entrada do Stream.

## Chaves de notificação

| Padrão | Tipo | Finalidade |
|---|---|---|
| `mottainai:v1:notification:stream` | Stream | Eventos de entrada. |
| `mottainai:v1:notification:data:{empresa}:{usuario}:{id}` | Hash | `id`, `title`, `body`, `priority`, `status`, `created_at`. |
| `mottainai:v1:notification:inbox:{empresa}:{usuario}` | Sorted set | IDs classificados por prioridade e, no empate, por data. |
| `mottainai:v1:notification:unread:{empresa}:{usuario}` | String numérica | Contador de notificações não lidas. |

O hash recebe TTL de 604.800 segundos (7 dias), sujeito à política de memória
do servidor. Escrita e reconciliação usam Lua para executar as operações
atomicamente. Repetir um ID enquanto o hash existe preserva conteúdo, estado e
TTL; após expiração, esse ID pode gerar nova notificação. Sem ID explícito,
o identificador derivado da entrada evita duplicação no reprocessamento da
mesma entrega, mas publicações distintas geram notificações distintas.

Listagem e marcação como lida reconciliam o índice e o contador com os hashes
existentes, removendo referências expiradas. A leitura não renova o TTL do
hash. A reconciliação percorre toda a caixa e seu custo cresce com o número
de entradas indexadas. O índice e o contador são expirados conforme o maior TTL
dos hashes ativos; se não restar nenhum, são removidos.

## Outros usos do Redis pela IA

O [keyspace da IA](https://github.com/Mottainai-One/Mottainai-IA/blob/021fdc0/app/cache/keyspace.py)
define também `mottainai:v1:rate-limit:...`, `:rag:...`,
`:alert-webhook-sent:...`, `:auth:revoked:...` e `:idempotency:...`.
O cache RAG tem TTL configurável, padrão 300 segundos. Locks de idempotência
podem permanecer após falha ambígua e exigem reconciliação; não trate essas
chaves como cache descartável sem avaliar o fluxo de escrita. A presença de
prefixos separados não comprova isolamento em instâncias diferentes.
