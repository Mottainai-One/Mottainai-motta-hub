# Mottainai Motta Hub

Aplicação web do catálogo de metadados e da biblioteca de documentação do Mottainai. A equipe consulta tabelas, campos e materiais de referência em um único lugar.

O Hub é uma ferramenta de consulta e documentação: ele não é o banco transacional do sistema, não executa SQL cadastrado e não altera tabelas de negócio.

## Estrutura

- [`motta-hub/`](motta-hub/README.md): aplicação Python, interface web, catálogo, testes e instruções de operação.
- [`render.yaml`](render.yaml): Blueprint de hospedagem do serviço web no Render.
- [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml): validação em Pull Requests e fluxo de deploy no Render após a CI.
- [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md): formulário para registrar contexto, validação, riscos e revisão.

## Executar localmente

Requer Python 3.12 ou compatível. No Windows PowerShell:

```powershell
cd motta-hub
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python render_build.py
python server.py --port 8766
```

Abra <http://127.0.0.1:8766>. O ambiente local inicia com o catálogo demonstrativo em SQLite. Não exponha o servidor local à Internet.

## Validar

Dentro da pasta `motta-hub/`:

```bash
python -m unittest -v test_server
python render_build.py
```

A CI executa esses comandos em Pull Requests e antes de solicitar implantação em `main`.

## Hospedagem e implantação

O Blueprint declara o serviço web no Render; a aplicação pode usar o PostgreSQL Aiven existente como persistência do catálogo publicado por meio de `HUB_DATABASE_URL`. O Render usa também `BOOTSTRAP_USERS_JSON` como variável privada do serviço; o GitHub usa `RENDER_DEPLOY_HOOK_URL` como segredo para acionar o deploy depois da CI. Nunca versionar valores dessas variáveis.

O repositório conter o Blueprint não prova que o serviço tenha sido criado, que os segredos estejam configurados ou que exista uma URL ativa. A implantação só é considerada concluída quando o serviço é sincronizado no Render, a CI aciona o deploy e `/healthz` responde com sucesso. Esta configuração não aloca recursos na AWS.

Veja o [README técnico da aplicação](motta-hub/README.md) para os papéis de acesso, persistência, variáveis e operação detalhados.
