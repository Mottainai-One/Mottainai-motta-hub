# Motta-hub

Catálogo local de metadados e biblioteca de documentação do Mottainai. Reúne tabelas, colunas, scripts documentais e materiais organizados por área.

**O hub não é um banco transacional e não executa SQL.** Alterações afetam o catálogo de metadados do Hub, com persistência no SQLite local e no PostgreSQL configurado para produção; não alteram tabelas operacionais nem executam scripts.

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

## Executar com Docker Compose

Com Docker Desktop ou Docker Engine ativo, na pasta `motta-hub` execute:

```bash
docker compose up --build --wait
```

Abra `http://127.0.0.1:8766`. O Compose inicia o Hub e um PostgreSQL local com volumes nomeados e aguarda os health checks. O banco usa credenciais demonstrativas e a porta fica disponível somente no loopback; esta configuração é para desenvolvimento, não produção. Pare os serviços com `docker compose down`; use `docker compose down --volumes` para remover também os dados locais.

Para reproduzir a validação executada na implantação:

```bash
python -m pip install -r requirements.txt
python -m unittest -v test_server
python render_build.py
```

## Deploy no Render

O Blueprint [`../render.yaml`](../render.yaml) configura o serviço web. O build instala `requirements.txt`, executa a suíte Python e recria o catálogo a partir da planilha incluída no repositório. O servidor escuta em `0.0.0.0:$PORT`, valida o domínio HTTPS do Render e oferece `/healthz` para o health check.

O arquivo Blueprint é configuração versionada; por si só, não comprova que o serviço esteja criado ou acessível. A automação de implantação está em [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml): PRs executam testes; pushes aprovados em `main` podem acionar o deploy após a CI. O Blueprint desativa deploy automático do provedor para que a Action controle a promoção. Configure o segredo `RENDER_DEPLOY_HOOK_URL` nas Actions do GitHub usando a URL privada obtida no Render. Sem esse segredo, a etapa de deploy informa que foi ignorada; não considere a aplicação publicada.

Em produção, configure `BOOTSTRAP_USERS_JSON` na página Environment do serviço. A variável deve conter as 12 contas com `email`, `role` e `passwordHash`; os papéis são 4 DBA, 4 FULLSTACK e 4 USER. Não inclua esse conteúdo no repositório. As senhas precisam permanecer como hashes bcrypt (`$2b$...`); o login não aceita senha em texto puro no campo `password_hash`.

Para alterar uma senha de validação, atualize o hash bcrypt em `BOOTSTRAP_USERS_JSON` e faça um novo deploy; não grave a senha em texto puro no banco.

O Blueprint mantém o serviço web no plano gratuito. Para persistir alterações mesmo quando esse serviço reiniciar ou sair do spin-down, configure `HUB_DATABASE_URL` com a URL de conexão do database PostgreSQL `MOTTAINAI`. São aceitos os formatos `postgresql://...` e `jdbc:postgresql://...`; o parâmetro JDBC `currentSchema` é ignorado porque o Hub grava explicitamente em `public`. Em produção, a aplicação exige essa variável e cria/atualiza as tabelas `public.hub_documentation_catalog` e `public.hub_table_catalog` durante a inicialização. O usuário PostgreSQL precisa ter acesso ao schema `public` e permissão para criar essas tabelas e índices. O SQL equivalente está em [`migrations/001_hub_persistent_catalog.sql`](migrations/001_hub_persistent_catalog.sql).

`hub_documentation_catalog` armazena o catálogo completo de seções/documentos em JSONB, com data e autor da última gravação. `hub_table_catalog` mantém o estado persistido de cada tabela do catálogo, incluindo colunas, descrições e marcadores de exclusão. No primeiro início com banco vazio, a aplicação grava a documentação e o tracking atuais como base; depois grava cada alteração feita no Hub. O catálogo operacional continua sendo metadado do Hub: nenhuma tabela de negócio é criada ou alterada.

No Render, adicione `HUB_DATABASE_URL` nas variáveis de ambiente do serviço, apontando para o database `mottainai` com conectividade de rede permitida pelo provedor do PostgreSQL. Use a URL privada quando o banco estiver na mesma rede privada. Não coloque a URL no repositório nem em mensagens. Sem a variável, o serviço de produção não inicia para evitar continuar aceitando alterações sem persistência durável.

Não há alocação ou deploy na AWS nesta configuração. A hospedagem prevista para este Hub é Render com PostgreSQL Aiven existente; ativá-la requer criar/sincronizar o Blueprint, provisionar os segredos no painel do Render e cadastrar o deploy hook como segredo do GitHub. Não publique contas, hashes, URLs de conexão ou hooks no Git.

