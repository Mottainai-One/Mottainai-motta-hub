# Desenvolvimento e Operações Ágeis — Mottainai

> Revisada em 31/10/2026. Reflete os repositórios locais consultados nesta data; valide o estado de branches, workflows e serviços antes de tratá-los como produção.

## Propósito

Este guia apresenta como a equipe planeja, implementa, valida, integra e opera mudanças no Mottainai. Cada repositório mantém sua CI; integrações passam por QA isolado; mudanças são promovidas por PR com evidência.

    Demanda e critérios de aceite
              ↓
    Branch → Pull Request → CIs existentes → revisão humana
              ↓
    QA local/CI → merge conforme regras → deploy, somente se configurado
              ↓
    Observabilidade, runbook e aprendizado

## Estado atual

| Capacidade | Estado verificado |
|---|---|
| GitHub Actions | Há workflows próprios de CI para API, banco, RPA, IA, frontend e mobile. Os checks variam por repositório. |
| PR Bot | Apoia criação/revisão de PRs. Não substitui checks, aprovação humana, resolução de conflitos ou branch protection. |
| QA com Docker Compose | Stack modular na branch feature/qa-api-integration de Mottainai-Banco-Operacional, pasta qa/: banco operacional isolado, overlays de API, IA, banco analítico e prévia do frontend. A branch não aparece integrada em main nas referências locais consultadas em 31/10/2026. |
| QA compartilhado | Ainda não implantado em servidor com URL e HTTPS. Os arquivos Compose preparam a stack, mas não provam disponibilidade remota. |
| Dados de QA | Separados da Aiven; usar dados sintéticos e credenciais exclusivas de QA. |
| Banco gerenciado | Aiven hospeda PostgreSQL. O plano Free não garante SLA nem capacidade de produção. |
| BI | Databricks Free Edition executa fluxo analítico diário nas camadas medalhão e alimenta dashboards. Não é tempo real. |
| AWS/Kubernetes | Direção futura. Não há cluster AWS de produção ou manifests Kubernetes ativos confirmados nos clones consultados. |
| Legado → operacional | origin/main do RPA declara sincronização a cada 5 minutos e reconciliação completa diária às 01:01 America/Sao_Paulo. Um clone local de branch de trabalho ainda mostra 30 minutos; conferir sempre a branch ativa. |
| Operacional → analítico | A configuração anterior declarou 02:00 em São Paulo, mas execuções observadas entre 28 e 30/10 ocorreram perto de 08:00; a de 30/10 falhou ao registrar o batch. A correção de cron UTC está na [PR RPA #13](https://github.com/Mottainai-One/Mottanai-RPA/pull/13), ainda não integrada. O fluxo só estará comprovado após um batch novo e correspondente execução Databricks. |

Não confundir build de imagem com implantação, Compose local com QA compartilhado, plano com serviço ativo ou CI verde com aceite de negócio.

## Repositórios e responsabilidades

| Repositório | Responsabilidade | Automação vista |
|---|---|---|
| [Mottainai-Spring-Api-SQL](https://github.com/Mottainai-One/Mottainai-Spring-Api-SQL) | API transacional | CI de build/teste e build de imagem QA |
| [Mottainai-Banco-Operacional](https://github.com/Mottainai-One/Mottainai-Banco-Operacional) | Schema operacional e migrations | CI de schema, dataLoad e checks SQL |
| [Mottanai-RPA](https://github.com/Mottainai-One/Mottanai-RPA) | Fluxos legado→operacional e operacional→analítico | Workflows schedule/manual e teste isolado |
| [Mottainai-IA](https://github.com/Mottainai-One/Mottainai-IA) | Serviço de IA | CI Python e build de imagem QA |
| [Mottainai-Frontend](https://github.com/Mottainai-One/Mottainai-Frontend) | Aplicação web | CI e build de imagem QA |
| [Mottainai-Mobile-Operacional](https://github.com/Mottainai-One/Mottainai-Mobile-Operacional) | Aplicativo Android | CI de build/teste e artefato QA |
| [Mottainai-Banco-Operacional — QA](https://github.com/Mottainai-One/Mottainai-Banco-Operacional/tree/feature/qa-api-integration/qa) | Compose integrador e validação de banco na branch de QA | CI de schema, dataLoad e analytics nessa branch |
| [mottainai-pr-bot](https://github.com/Mottainai-One/mottainai-pr-bot) | GitHub App de apoio a PR | Webhook/App configurado no próprio repo |
| [Mottainai-Hub](https://github.com/Mottainai-One/Mottainai-Hub) | Documentação central | Arquitetura e operação |

Cada repositório mantém seus workflows. Uma CI de QA ou um workflow recém-criado não substitui checks já exigidos.

## Fluxo recomendado

1. Registrar objetivo, contexto, critérios de aceite, responsável e riscos.
2. Criar branch de tópico: feature/, fix/ ou docs/. Não usar prefixo codex/.
3. Fazer mudança coesa e preservar todas as CIs existentes.
4. Abrir PR com resumo, evidências, impactos e rollback se necessário.
5. Passar checks requeridos, resolver conflitos e obter revisões humanas configuradas.
6. Validar em QA mudanças que cruzam componentes/dados. Build de imagem não é teste integrado.
7. Mesclar conforme política do repositório; deploy apenas se houver workflow ativo.
8. Acompanhar saúde, atualizar runbook e registrar aprendizado.

Veja [Fluxo ágil e operação](07-fluxo-agil-e-operacao.md).

## Mapa

| Página | Conteúdo |
|---|---|
| [01 — Docker e QA](01-docker.md) | Compose, comandos e limites |
| [02 — Kubernetes](02-kubernetes.md) | Evolução planejada para produção |
| [03 — Cloud](03-cloud.md) | Serviços e estado de implantação |
| [04 — CI/CD](04-ci-cd.md) | Workflows e preservação de checks |
| [05 — Code Review e PR Bot](05-code-review-pr.md) | Revisão, aprovação e merge |
| [06 — RPA e operação de dados](06-automation-hub.md) | Fluxos, cadência e recuperação |
| [07 — Fluxo ágil](07-fluxo-agil-e-operacao.md) | Planejamento, DoR/DoD e métricas |

Atualizar primeiro o repositório que contém o workflow/manifesto executável e refletir aqui após revisão. Marcar claramente: implementado, validado em QA, implantado ou planejado.
