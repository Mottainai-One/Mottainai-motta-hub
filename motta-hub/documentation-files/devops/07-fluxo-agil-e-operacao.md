# Fluxo ágil e modelo de operação

## Da demanda à entrega

### Refinamento

Registrar problema, área afetada, resultado esperado, critérios de aceite verificáveis, componentes/dependências, riscos de dados/segurança/disponibilidade/custo, responsáveis e evidência. Demanda sem critério de aceite retorna ao refinamento.

### Planejamento e desenvolvimento

Dividir iniciativa em incrementos revisáveis. Priorizar desbloqueio de qualidade/operação antes de infraestrutura nova. Usar branches feature/, fix/, docs/ e chore/; não usar prefixo codex/ em branches compartilhadas.

Manter configuração por ambiente, credenciais fora do Git e contratos alinhados entre produtor, consumidor, CI e documentação.

### Revisão e integração

Abrir PR coesa, preservar CIs existentes, atender checks/revisões, resolver conflitos e anexar validações. Não remover workflows para contornar falha.

### Validação por risco

- Unitário/lint/build para mudança isolada.
- Integração para fronteiras API/banco, RPA e serviços.
- Compose para fluxos multi-serviço.
- Smoke test após deploy.
- Aceite de negócio para KPI, regra ou comportamento de usuário.

Imagem construída não é evidência de ponta a ponta. Registrar o que não foi testado e por quê.

### Release e operação

Deploy produtivo depende de infraestrutura/workflow aprovados. Confirmar secrets/config, migration, backup/restore, healthchecks, alertas, responsável e rollback. Merge, publicação de artefato e implantação são eventos diferentes.

## Definition of Ready

Objetivo, usuário/área afetada, critérios testáveis, escopo/repos, dependências/riscos, dados/ambiente de teste, prioridade e responsável acordados.

## Definition of Done

- Critérios atendidos com evidência.
- CI obrigatória passou.
- Revisão humana configurada foi registrada e PR integrada.
- Documentação/runbook/contratos atualizados.
- QA apropriado executado ou limites aceitos explicitamente.
- Mudança operacional tem observabilidade e rollback.
- Sem segredo ou dado real de produção em Git/QA.
- Deploy confirmado quando a entrega inclui deploy.

## Métricas

Estabelecer baseline antes de metas.

| Indicador | Definição |
|---|---|
| Lead time | Primeiro commit até produção; se sem deploy, acompanhar até merge/QA e marcar o limite |
| Frequência de entrega | Deploys por período, separados de merges |
| Falha de mudança | Mudanças com rollback/hotfix ÷ deploys |
| Recuperação | Tempo entre detecção e restabelecimento |
| Saúde da CI | Duração, sucesso e causas recorrentes por repo |
| Integração | Atraso legado→operacional, cutoff analítico, reconciliação e falhas |
| QA | Cobertura de integração e defeitos antes/depois de release |

Revisar tendências em retrospectivas. Usar métricas para melhorar o processo, não para ranquear pessoas. Este guia não presume ferramenta de quadro nem cadência de cerimônias não definida pela equipe.
