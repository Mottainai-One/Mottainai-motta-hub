# Motta-hub

Catálogo local de metadados e biblioteca de documentação do Mottainai. Reúne tabelas, colunas, scripts documentais e materiais organizados por área.

**O hub não é um banco transacional e não executa SQL.** Alterações afetam o catálogo SQLite local; não alteram o banco de origem nem executam scripts.

## Executar

Na pasta do projeto, execute:

```bash
python server.py --port 8766
```

Abra `http://127.0.0.1:8766`. O projeto inclui `app.js` compilado; o backend usa a biblioteca padrão do Python. O servidor escuta somente em `127.0.0.1`. Não exponha o app à internet sem revisão de segurança e autenticação.

Mantenha o `catalog.sqlite3` incluído. Se o banco não existir, o servidor inicializa dados de demonstração, não o catálogo completo da planilha.

## Permissões

| Perfil | Consultar | Criar tabela | Alterar colunas diretamente | Solicitar colunas | Revisar pedidos |
|---|---:|---:|---:|---:|---:|
| Usuário | Sim | Não | Não | Não | Não |
| FullStack | Sim | Não | Não | Sim | Cancelar pedido aberto com justificativa |
| DBA | Sim | Sim | Sim | Não | Editar nome/descrição, comentar, aprovar ou recusar |

Todos os FullStacks veem todos os pedidos; todos os DBAs podem revisar qualquer pedido.

## Solicitações e notificações

FullStack pode solicitar uma ou mais colunas em uma tabela existente, com motivo obrigatório e descrição opcional por coluna. Só pode haver uma solicitação aberta por tabela. A aprovação adiciona todas as colunas ao catálogo na mesma operação. DBA pode editar somente nomes e descrições, comentar mantendo o pedido aberto, aprovar ou recusar com justificativa. Qualquer FullStack pode cancelar com justificativa.

As notificações são internas ao hub e chegam pelo ícone no header: abertura e cancelamento avisam DBAs; comentários, aprovações e recusas avisam FullStacks. Não há integração de SMS ou WhatsApp.

## Documentação

- [`documentation-source/`](documentation-source/README.md): fonte organizada do acervo.
- [`documentation-files/`](documentation-files/): arquivos servidos pelo site, gerados da fonte.
- [`documentations.json`](documentations.json): índice pesquisável gerado pelo importador.
- [`docs/`](docs/README.md): documentação técnica do próprio aplicativo.
- [Índice da biblioteca por área](docs/INDICE-BIBLIOTECA.md).

Depois de editar `documentation-source/`, execute `python import_documentations.py` na raiz do projeto. O importador verifica sinais de credenciais e interrompe a geração quando encontra conteúdo suspeito; use variáveis demonstrativas em exemplos.

## Fonte do catálogo

A planilha incluída contém 139 tabelas e 883 campos: 80 tabelas/723 campos no schema `mottainai` e 59 tabelas/160 campos no schema `mottainai_analytics`. O catálogo local também preserva o schema `teste`; as contagens podem mudar com atualizações autorizadas.

## Scripts documentais

Somente DBA pode cadastrar scripts `ALTER TABLE`. O servidor valida o envelope e a tabela alvo, mas não é um parser completo de SQL. Scripts são armazenados como texto e nunca executados. Não inclua credenciais, dados pessoais ou resultados de consultas.

## Desenvolvimento

O build do frontend usa `npm run build`; a suíte da API pode ser executada com `npm run test:api`.

## Deploy no Render

O Blueprint [`../render.yaml`](../render.yaml) configura o serviço web. O build executa a suíte Python e recria o catálogo a partir da planilha incluída no repositório. O servidor escuta em `0.0.0.0:$PORT`, valida o domínio HTTPS do Render e oferece `/healthz` para o health check.

No primeiro deploy, o Render gera as senhas de `BOOTSTRAP_DBA_PASSWORD` e `BOOTSTRAP_FULLSTACK_PASSWORD`. Consulte-as no painel do serviço e compartilhe-as com as pessoas autorizadas pelos canais internos da equipe. O ambiente de produção cria somente as contas correspondentes a `BOOTSTRAP_DBA_EMAIL` e `BOOTSTRAP_FULLSTACK_EMAIL`; não use credenciais de demonstração em produção.

O Blueprint usa o plano gratuito para permitir a avaliação sem custo. O sistema de arquivos desse plano é efêmero: o catálogo é reconstruído no deploy, mas alterações feitas depois podem ser perdidas quando a instância reiniciar ou for substituída. Para preservar alterações do catálogo, conecte um disco persistente em `/var/data` e configure `CATALOG_DB_PATH=/var/data/catalog.sqlite3` em um plano que suporte discos persistentes.
