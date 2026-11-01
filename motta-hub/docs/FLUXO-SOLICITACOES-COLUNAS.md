# Solicitações de colunas e central de notificações

## Objetivo

FullStack solicita a inclusão de uma ou mais colunas em uma tabela existente. DBA revisa o pedido; a aprovação acrescenta as colunas ao catálogo local. O hub não executa SQL nem altera o banco de origem.

## Papéis

- **DBA:** pode alterar o catálogo diretamente e revisar qualquer solicitação. Pode editar apenas nome e descrição das colunas, comentar mantendo o pedido aberto, aprovar o pedido inteiro ou recusá-lo com justificativa.
- **FullStack:** consulta e abre solicitações; não cria tabelas nem altera colunas diretamente, e não responde aos comentários do DBA. Qualquer FullStack pode cancelar uma solicitação aberta com justificativa.
- **Usuário:** consulta o catálogo, sem ações de alteração ou solicitação.

Todos os FullStacks veem os pedidos do cargo; todos os DBAs podem visualizar e decidir qualquer pedido.

## Campos e bloqueios

Cada pedido contém uma tabela existente, um motivo obrigatório e uma lista de colunas. O nome de cada coluna é obrigatório e a descrição é opcional. Não há campo de script. Só pode existir um pedido aberto por tabela; depois do encerramento é possível abrir outro. O servidor também bloqueia uma solicitação exatamente igual quando ainda está aberta.

## Ações e status

- **Aberta:** aguardando decisão. Comentários do DBA podem manter o pedido aberto.
- **Aprovada:** o pedido inteiro é aprovado e as colunas são inseridas no catálogo na mesma transação.
- **Recusada:** exige justificativa e encerra o pedido.
- **Cancelada:** qualquer FullStack pode encerrar com justificativa. O registro fica preservado, mas não entra na lista das últimas cinco aprovadas/recusadas.

O histórico de cada pedido mostra as cinco ações mais recentes.

## Central interna de notificações

Os avisos aparecem no ícone de notificações do header, dentro do Motta-hub. Ao abrir um pedido, a central avisa os DBAs, que podem modificar tabelas. Comentários, aprovações e recusas avisam os FullStacks; cancelamentos avisam os DBAs. Não há envio por SMS ou WhatsApp.

## Listas

- **DBA:** solicitações não respondidas e últimas cinco aprovadas/recusadas.
- **FullStack:** solicitações em processamento e últimas cinco aprovadas/recusadas.

As mudanças são feitas no catálogo SQLite local, sem alterar o banco de origem.
