# Entrega — Desenvolvimento e Operações Ágeis

## Escopo

Esta entrega atende ao projeto Mottainai e acompanha os requisitos da disciplina no documento de 14/05/2026. A alocação de infraestrutura na AWS está expressamente fora do escopo desta execução. O caminho de hospedagem preparado aqui usa Render e o PostgreSQL Aiven já utilizado pelo projeto.

## Matriz de atendimento

| Requisito | Evidência clicável | Estado e limite da evidência |
|---|---|---|
| **M1 — Code Review, Pull Request e aprovações** | [PR #20 de revisão DevOps](https://github.com/Mottainai-One/Mottainai-Hub/pull/20); [PR #4 desta entrega](https://github.com/Mottainai-One/Mottainai-motta-hub/pull/4); [CI da PR #4](https://github.com/Mottainai-One/Mottainai-motta-hub/actions/runs/41457889250) | **Atendido.** PR #20 foi integrada com duas aprovações humanas; a PR #4 desta entrega também recebeu duas aprovações humanas (TutuHub123 e bellathecreator), teve o check Test and build aprovado e foi integrada. O job de deploy Render da PR #4 foi ignorado e não é evidência de hospedagem ativa. |
| **M2 — Nuvem para hospedar o projeto** | [Blueprint Render](../../render.yaml); [instruções de hospedagem](../../README.md); [inventário de nuvem do projeto](https://github.com/Mottainai-One/Mottainai-Hub/blob/main/Docs/devops/03-cloud.md); [health check ao vivo](https://mottainai-motta-hub.onrender.com/healthz) | **Atendido para o Motta Hub; parcial no runtime de negócio.** O endpoint Render respondeu `HTTP 200` e `{"ok": true}` nesta auditoria. Aiven hospeda PostgreSQL e Databricks hospeda o fluxo de BI. O deploy das aplicações de negócio na AWS está fora do escopo desta entrega. |
| **M3 — Containers e orquestração** | [Dockerfile do Hub](../Dockerfile); [Compose do Hub e PostgreSQL](../compose.yaml); [execução integrada do Compose e health checks](https://github.com/Mottainai-One/Mottainai-motta-hub/actions/runs/41457889250); [workflow de CI/CD](../../.github/workflows/ci-cd.yml) | **Implementado e validado na CI.** Docker Compose coordena o Hub e PostgreSQL. A execução da PR #4 construiu e iniciou ambos, aguardou os health checks e consultou `/healthz` e a API autenticada de documentações. Kubernetes não está implantado; Compose é a tecnologia de orquestração usada. |
| **E1 — README completo** | [README principal](../../README.md); [README técnico do Hub](../README.md) | **Atendido.** O README principal apresenta finalidade, estrutura, execução, validação, hospedagem, secrets e limites de implantação; o README técnico detalha acesso e persistência. |
| **E2 — Template de Pull Request aplicado** | [Template de PR](../../.github/PULL_REQUEST_TEMPLATE.md); esta PR de correção de pipeline | **Atendido.** O template já está na branch base e suas seções foram aplicadas manualmente a esta PR. A PR #4 adicionou o template, mas não podia recebê-lo da base porque o arquivo ainda não existia; sua descrição foi preenchida manualmente com seções equivalentes. |
| **E3 — Pipeline para implantação** | [Workflow de CI](../../.github/workflows/ci-cd.yml); [Blueprint Render com deploy após checks aprovados](../../render.yaml); [documentação oficial `autoDeployTrigger`](https://render.com/docs/blueprint-spec) | **Pipeline configurado; publicação automática a confirmar após sincronizar o Blueprint.** A Action valida PRs e `main`. O Blueprint usa `autoDeployTrigger: checksPass`; após sincronizado no serviço Render, novos commits vinculados são publicados pelo Render somente depois dos checks do GitHub passarem. O job antigo usava `RENDER_DEPLOY_HOOK_URL`, mas o log da execução [#41491871404](https://github.com/Mottainai-One/Mottainai-motta-hub/actions/runs/41491871404) mostra que ele ignorou a publicação por ausência do secret. O novo fluxo não depende desse hook. A alocação de runtime do negócio na AWS permanece fora do escopo. |
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

1. A PR #4 desta entrega foi revisada por duas pessoas e integrada; o check Test and build passou. O log mostra que o antigo job de deploy foi ignorado porque o secret `RENDER_DEPLOY_HOOK_URL` não estava configurado.
2. Sincronizar o Blueprint atualizado no Render e confirmar `After CI Checks Pass` (`autoDeployTrigger: checksPass`) para o serviço conectado ao repositório.
3. Manter `BOOTSTRAP_USERS_JSON` e `HUB_DATABASE_URL` como variáveis privadas do serviço Render; não incluir valores no Git nem nesta documentação.
4. Após a integração desta PR, confirmar uma publicação acionada por commit em `main` somente depois dos checks passarem; validar `https://<serviço>/healthz` e guardar o link do deploy.
5. Registrar URL pública, commit implantado e execução dos checks, sem publicar valores secretos. O health check atual respondeu `{"ok":true}` nesta auditoria, mas ainda é necessário registrar uma publicação automatizada depois da sincronização do Blueprint.

O health check ao vivo comprova que o Hub está hospedado e respondendo no Render. Ele não comprova que a alteração `checksPass` desta PR já foi sincronizada nem que um commit desta PR foi publicado automaticamente; essa confirmação fica pendente após merge e sincronização do Blueprint. A execução da CI da PR #4 fornece evidência do fluxo integrado Docker Compose.
