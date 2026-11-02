# Entrega — Desenvolvimento e Operações Ágeis

## Escopo

Esta entrega atende ao projeto Mottainai e acompanha os requisitos da disciplina no documento de 14/05/2026. A alocação de infraestrutura na AWS está expressamente fora do escopo desta execução. O caminho de hospedagem preparado aqui usa Render e o PostgreSQL Aiven já utilizado pelo projeto.

## Matriz de atendimento

| Requisito | Evidência clicável | Estado e limite da evidência |
|---|---|---|
| **M1 — Code Review, Pull Request e aprovações** | [PR de revisão da documentação de DevOps](https://github.com/Mottainai-One/Mottainai-Hub/pull/20); [aprovação TutuHub123](https://github.com/Mottainai-One/Mottainai-Hub/pull/20#pullrequestreview-5721047375); [aprovação Joao0524](https://github.com/Mottainai-One/Mottainai-Hub/pull/20#pullrequestreview-5721056081) | **Atendido.** PR #20 foi aprovada por duas pessoas e integrada. A PR desta entrega deve passar pelas aprovações humanas configuradas antes de ser integrada. |
| **M2 — Nuvem para hospedar o projeto** | [Blueprint Render](https://github.com/Mottainai-One/Mottainai-motta-hub/blob/feature/agile-delivery-pipeline/render.yaml); [instruções de hospedagem](../../README.md); [inventário de nuvem do projeto](https://github.com/Mottainai-One/Mottainai-Hub/blob/main/Docs/devops/03-cloud.md) | **Parcial.** Aiven hospeda PostgreSQL e Databricks hospeda o fluxo de BI. O Blueprint web está configurado no branch desta entrega, mas não há evidência de serviço Render ativo. Para concluir o aceite de hospedagem, é necessário sincronizar o Blueprint, configurar os segredos e conferir `/healthz`. Não foi feita alocação AWS. |
| **M3 — Containers e orquestração** | [Dockerfile do Hub](../Dockerfile); [Compose do Hub e PostgreSQL](../compose.yaml); [verificação de saúde no workflow](../../../.github/workflows/ci-cd.yml) | **Implementado com validação automatizada.** Docker Compose coordena o Hub e PostgreSQL. GitHub Actions constrói e inicia os dois serviços, espera pelos health checks e consulta `/healthz` e `/api/documentations`. A execução publicada da CI será a evidência runtime. Kubernetes não está implantado; Compose é a tecnologia de orquestração usada. |
| **E1 — README completo** | [README principal](../../README.md); [README técnico do Hub](../README.md) | **Atendido.** O README principal apresenta finalidade, estrutura, execução, validação, hospedagem, secrets e limites de implantação; o README técnico detalha acesso e persistência. |
| **E2 — Template de Pull Request aplicado** | [Template de PR](../../.github/PULL_REQUEST_TEMPLATE.md) | **Atendido nesta entrega** quando a PR é aberta com as seções Contexto, Alterações, Validação, Risco e Revisão do template. |
| **E3 — Pipeline para implantação** | [Workflow de CI/CD](../../.github/workflows/ci-cd.yml); [guia oficial do Render para deploy hook com GitHub Actions](https://render.com/docs/deploy-hooks) | **Implementado, ativação pendente.** A Action testa PRs e `main`; após CI, aciona o Render somente em `main` ou por execução manual solicitada. O deploy só é enviado quando `RENDER_DEPLOY_HOOK_URL` estiver configurado como secret. Sem serviço/secret, a Action informa que não publicou. |
| **Documento de entrega detalhado** | Este documento | **Atendido.** Cada item aponta para o artefato ou registro de aprovação correspondente. |

## Fluxo de trabalho

1. Registrar objetivo, critérios de aceite, escopo, riscos e responsável antes do desenvolvimento.
2. Abrir branch de tópico e manter o commit em inglês no padrão Conventional Commits.
3. Usar o template de PR para registrar mudanças, validações, riscos e plano de implantação.
4. Exigir CI aprovada e revisão humana configurada antes de integrar.
5. Validar mudanças que cruzam serviços na stack Compose com dados e credenciais de QA isolados.
6. Promover à nuvem apenas após a aprovação da PR; monitorar o deploy e validar o health check.

O processo, as definições de Ready/Done e as métricas estão detalhados no [guia de fluxo ágil e operação](https://github.com/Mottainai-One/Mottainai-Hub/blob/main/Docs/devops/07-fluxo-agil-e-operacao.md). A visão de CI e separação entre build, QA e deploy está no [guia de CI/CD](https://github.com/Mottainai-One/Mottainai-Hub/blob/main/Docs/devops/04-ci-cd.md).

## Etapas necessárias para o aceite integral de nuvem

1. Revisar e integrar a PR deste branch após CI e aprovações humanas.
2. Criar/sincronizar o Blueprint no Render e configurar `BOOTSTRAP_USERS_JSON` e `HUB_DATABASE_URL` no painel do serviço; esses valores não devem ir para Git ou para este documento.
3. Criar um deploy hook no serviço Render e salvá-lo no GitHub como secret `RENDER_DEPLOY_HOOK_URL`.
4. Rodar o workflow `CI and Render deployment` em `main`; conferir o resultado do deploy e `https://<serviço>/healthz`.
5. Registrar a URL e a execução de deploy aprovada, sem publicar valores secretos.

Até essa ativação, o Blueprint e o workflow são configuração versionada, não prova de aplicação publicada. A stack Compose também precisa ser iniciada em uma máquina com Docker autorizado para demonstrar o fluxo integrado completo.

