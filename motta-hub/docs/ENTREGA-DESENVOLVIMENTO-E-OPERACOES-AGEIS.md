# Entrega — Desenvolvimento e Operações Ágeis

## Escopo

Esta entrega atende ao projeto Mottainai e acompanha os requisitos da disciplina no documento de 14/05/2026. A alocação de infraestrutura na AWS está expressamente fora do escopo desta execução. O caminho de hospedagem preparado aqui usa Render e o PostgreSQL Aiven já utilizado pelo projeto.

## Matriz de atendimento

| Requisito | Evidência clicável | Estado e limite da evidência |
|---|---|---|
| **M1 — Code Review, Pull Request e aprovações** | [PR #20 de revisão DevOps](https://github.com/Mottainai-One/Mottainai-Hub/pull/20); [PR #4 desta entrega](https://github.com/Mottainai-One/Mottainai-motta-hub/pull/4); [CI da PR #4](https://github.com/Mottainai-One/Mottainai-motta-hub/actions/runs/41457889250) | **Atendido.** PR #20 foi integrada com duas aprovações humanas; a PR #4 desta entrega também recebeu duas aprovações humanas (TutuHub123 e bellathecreator), teve o check Test and build aprovado e foi integrada. O job de deploy Render da PR #4 foi ignorado e não é evidência de hospedagem ativa. |
| **M2 — Nuvem para hospedar o projeto** | [Blueprint Render](https://github.com/Mottainai-One/Mottainai-motta-hub/blob/main/render.yaml); [instruções de hospedagem](../../README.md); [inventário de nuvem do projeto](https://github.com/Mottainai-One/Mottainai-Hub/blob/main/Docs/devops/03-cloud.md) | **Parcial.** Aiven hospeda PostgreSQL e Databricks hospeda o fluxo de BI. O Blueprint web está configurado na `main`, mas não há evidência de serviço Render ativo. Para concluir o aceite de hospedagem, é necessário sincronizar o Blueprint, configurar os segredos e conferir `/healthz`. Não foi feita alocação AWS. |
| **M3 — Containers e orquestração** | [Dockerfile do Hub](../Dockerfile); [Compose do Hub e PostgreSQL](../compose.yaml); [execução integrada do Compose e health checks](https://github.com/Mottainai-One/Mottainai-motta-hub/actions/runs/41457889250); [workflow de CI/CD](../../.github/workflows/ci-cd.yml) | **Implementado e validado na CI.** Docker Compose coordena o Hub e PostgreSQL. A execução da PR #4 construiu e iniciou ambos, aguardou os health checks e consultou `/healthz` e a API autenticada de documentações. Kubernetes não está implantado; Compose é a tecnologia de orquestração usada. |
| **E1 — README completo** | [README principal](../../README.md); [README técnico do Hub](../README.md) | **Atendido.** O README principal apresenta finalidade, estrutura, execução, validação, hospedagem, secrets e limites de implantação; o README técnico detalha acesso e persistência. |
| **E2 — Template de Pull Request aplicado** | [Template de PR](../../.github/PULL_REQUEST_TEMPLATE.md) | **Atendido com adaptação.** A PR #4 incluiu contexto, alterações, validação e riscos/implantação; também registrou a revisão humana, e adicionou uma matriz disciplinar à descrição. |
| **E3 — Pipeline para implantação** | [Workflow de CI/CD](../../.github/workflows/ci-cd.yml); [guia oficial do Render para deploy hook com GitHub Actions](https://render.com/docs/deploy-hooks) | **Pipeline implementado; publicação ainda pendente.** A Action valida PRs e `main` e tem um job de deploy Render após CI. Na execução da PR #4, Test and build passou e Deploy to Render foi ignorado; portanto, a implantação não foi comprovada. A ativação exige serviço Render sincronizado e secret `RENDER_DEPLOY_HOOK_URL` configurado. |
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

1. A PR #4 desta entrega foi revisada por duas pessoas e integrada; o check Test and build passou. O job Deploy to Render foi ignorado.
2. Criar/sincronizar o Blueprint no Render e configurar `BOOTSTRAP_USERS_JSON` e `HUB_DATABASE_URL` no painel do serviço; não incluir esses valores no Git nem nesta documentação.
3. Criar um deploy hook para o serviço e salvá-lo no GitHub como secret `RENDER_DEPLOY_HOOK_URL`.
4. Executar o workflow `CI and Render deployment` em `main` após configurar o secret; confirmar a publicação e consultar `https://<serviço>/healthz`.
5. Registrar a URL pública e o link da execução de deploy aprovada, sem publicar valores secretos.

Até a ativação, o Blueprint e o workflow são configuração versionada, não prova de aplicação publicada. A execução da CI da PR #4 já fornece evidência do fluxo integrado Docker Compose; permanece pendente a implantação hospedada no Render e sua confirmação por `/healthz`.

