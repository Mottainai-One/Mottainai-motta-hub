# Docker e ambiente de QA

## Objetivo e estado

Docker Compose fornece ambiente reproduzível para validar integrações sem conectar QA aos bancos reais da Aiven. O Compose de referência está na pasta qa/ da branch feature/qa-api-integration do repositório Mottainai-Banco-Operacional. Nas referências locais de 31/10/2026, essa branch ainda não aparece integrada em main. A stack é local/CI; para acesso da equipe ainda faltam servidor, domínio e HTTPS.

Não publicar PostgreSQL, MongoDB ou Redis diretamente na Internet.

## Componentes

| Arquivo | Conteúdo |
|---|---|
| qa/compose.yaml | PostgreSQL 15 operacional isolado, volume, rede interna e verificador SQL |
| qa/compose.api.yaml | API Spring e Mailpit QA |
| qa/compose.ia.yaml | PostgreSQL analítico QA, MongoDB, Redis e serviço IA |
| qa/compose.frontend.yaml | Prévia frontend no profile preview |
| qa/compose.*.local.yaml | Overrides locais de portas e acesso |
| qa/verify.sql | Verificações pelo usuário restrito de aplicação |
| qa/.env.example | Nomes de variáveis, sem credenciais reais |

Android não roda como serviço Compose. A RPA tem teste em container sem rede e sem acesso a banco real; Compose não ativa schedule produtivo.

## Segurança e requisitos

- Docker Desktop com Compose V2.
- Usar a branch feature/qa-api-integration de Mottainai-Banco-Operacional e clonar os projetos requeridos lado a lado, ou configurar caminhos QA_*_BUILD_CONTEXT.
- Copiar qa/.env.example para qa/.env e preencher senhas exclusivas, fortes e diferentes.
- Não versionar .env, reutilizar credenciais Aiven ou compartilhar segredos em logs/screenshots/PRs.
- Usar dados sintéticos, nunca dados de produção.
- Compose base não publica portas de banco; overrides *.local.yaml são apenas locais.
- Volume persiste entre reinícios; remover volume apaga os dados QA.

## Banco operacional: iniciar e verificar

Na raiz do clone Mottainai-Banco-Operacional, na branch de QA:

    Copy-Item qa/.env.example qa/.env
    # Preencha qa/.env localmente; não compartilhe valores nem faça commit.
    docker compose --env-file qa/.env -f qa/compose.yaml -f qa/compose.local.yaml up -d postgres
    docker compose --env-file qa/.env -f qa/compose.yaml --profile verify run --rm verify

Porta local opcional: 127.0.0.1:55432. Healthcheck confirma schema e role; verify testa permissões do login de aplicação. Scripts init não são reaplicados a volumes existentes; alterações seguem por migration.

## API e IA

Depois de configurar as variáveis em .env, a composição local combina:

    docker compose --env-file qa/.env -f qa/compose.yaml -f qa/compose.api.yaml -f qa/compose.ia.yaml -f qa/compose.local.yaml -f qa/compose.api.local.yaml -f qa/compose.ia.local.yaml up -d --build

Ver nomes de variáveis, portas e perfis no [README de QA](https://github.com/Mottainai-One/Mottainai-Banco-Operacional/blob/feature/qa-api-integration/qa/README.md). Para frontend, incluir qa/compose.frontend.yaml e o override local com profile preview.

Build de imagem e health/readiness validam empacotamento/inicialização, não todos os fluxos de negócio nem integração completa.

## Encerrar preservando dados

Use os mesmos arquivos Compose empregados para iniciar:

    docker compose --env-file qa/.env -f qa/compose.yaml -f qa/compose.local.yaml down

Não usar -v se quiser manter o volume. Remover volume é ação destrutiva, somente para ambiente descartável após conferir o alvo.

## CI de containers versus QA integrado

Workflows API QA container, IA QA container e Frontend QA container constroem imagens. Isso não prova que todos os serviços subiram juntos. A QA Compose integrada ainda precisa de servidor/URL para ficar acessível à equipe toda.
