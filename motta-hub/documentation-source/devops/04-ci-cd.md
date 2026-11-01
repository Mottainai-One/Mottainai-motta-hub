# CI/CD — validação e implantação

## Modelo

GitHub Actions valida mudanças em workflows independentes por repositório. Cada projeto mantém checks e gatilhos próprios. **Não substituir, remover ou desabilitar CI existente para fazer uma PR passar.** Corrigir o workflow com falha preservando os demais checks.

CI valida código; build valida empacotamento; QA integrada valida serviços juntos; CD implanta. Uma etapa não comprova a seguinte.

## Workflows observados

Nomes vistos nos clones locais em 31/10/2026; conferir branch principal para estado vigente.

| Repositório | Workflows | Função |
|---|---|---|
| Spring API | ci.yml, qa-container.yml | Build/teste e checks; QA constrói imagem |
| Banco Operacional | ci.yml | Schema, dataLoad e checks SQL/documentação/segredos |
| RPA | legacy-to-operational.yml, operational-to-analytics.yml, qa.yml | Sincronizações e teste isolado |
| IA | ci.yml, qa-container.yml | Checks Python/testes e build de imagem |
| Frontend | ci.yml, qa-container.yml | Build/test/lint e imagem QA |
| Mobile | ci.yml, qa-build.yml | Build/teste/lint Android e artefato |
| Banco Operacional, branch QA | ci.yml | Schema, dataLoad e objetos analíticos adicionados na branch de integração QA |

Jobs e required checks devem ser consultados no PR/workflow atual. A lista varia por repo.

## Fluxo de PR

1. CI roda em push/PR segundo o workflow.
2. Revisores analisam semântica, segurança, impacto e evidência.
3. Autor corrige cada falha preservando checks independentes.
4. Conflitos resolvidos; checks reexecutados no estado atualizado.
5. Merge depende de checks e aprovações configurados naquele repo.
6. Deploy ocorre só se houver CD ativo.

PRs recentes mostraram necessidade de duas aprovações. Confirmar regras e checks em Settings → Branches/Rulesets; não presumir política global.

## Diagnóstico sem enfraquecer CI

- Abrir o job falho e localizar a causa nos logs.
- Reproduzir o check afetado localmente quando aplicável.
- Corrigir o job/código mantendo workflows e gatilhos.
- Não apagar CI, renomear required check sem atualizar proteção, esconder erros com continue-on-error ou contornar branch protection.
- Reexecutar checks e registrar evidência na PR.

## QA, CD e secrets

Workflows qa-container.yml constroem imagens; RPA QA roda testes isolados. Isso não significa deploy automático para QA compartilhado. Ver [Docker e QA](01-docker.md).

Não há CD AWS/Kubernetes confirmado nos arquivos examinados. render.yaml do PR Bot é configuração, não evidência de deploy. Documentar CD após confirmar gatilho, identidade, ambiente, aprovação e rollout.

Usar GitHub Secrets sem imprimir valores em logs, permissões mínimas e segredos QA separados dos de produção. Acompanhar atualizações de actions/dependências por PR.

## Métricas

Medir duração e sucesso da CI, causas recorrentes, tempo de recuperação, tempo de PR e releases. Criar baseline por projeto e separar falhas de código de falhas de infraestrutura.
