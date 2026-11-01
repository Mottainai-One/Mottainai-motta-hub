# Code Review, Pull Requests e PR Bot

## Propósito

A PR registra objetivo, escopo, validação e riscos. Automação ajuda a resumir e revisar; responsabilidade técnica e aprovação continuam com pessoas autorizadas.

## Papel do PR Bot

O repositório mottainai-pr-bot documenta um GitHub App que pode criar PRs, analisar diffs via Gemini, sugerir review/descrição e aplicar descrição após label configurado. Isso depende de app, webhook, permissões e configuração ativos.

O bot não substitui required checks, não resolve todos os conflitos e não garante regras uniformes entre repositórios. Auto-merge só ocorre se estiver habilitado e todas as proteções forem satisfeitas.

## Branches e escopo

Usar branches de tópico curtas: feature/, fix/, docs/ ou chore/. Não usar prefixo codex/ em branches compartilhadas. Uma PR deve tratar mudança coesa e apontar documentação afetada.

## Conteúdo mínimo

1. Objetivo, contexto e critérios de aceite.
2. Resumo e componentes afetados.
3. Validações e evidências.
4. Impactos em schema, dados, segurança, custo e disponibilidade.
5. Plano de migração/release/rollback, se necessário.
6. Limitações e dependências conhecidas.

## Revisão e merge

- Todos os checks obrigatórios passam; CI nova não substitui antigas.
- Resolver conflitos preservando intenção de main e feature; envolver responsáveis.
- Obter aprovações/checks configurados no repositório.
- Review do bot não conta como aprovação humana quando GitHub exige pessoas com write access.
- Seguir política de merge sem contornar proteção.
- Após merge, confirmar CI da branch principal e deploy, quando houver.

## Revisão por risco

| Mudança | Questões |
|---|---|
| Banco/migration | Compatibilidade, rollback, idempotência, transação, RLS e permissões |
| RPA/pipeline | Origem/destino, retries, cutoff, privacidade, reconciliação e concorrência |
| API/web/mobile | Contratos, autenticação, autorização e falhas |
| Docker/infra | Portas, secrets, recursos, healthchecks, rede e persistência |
| CI | Preservação de workflows, menor permissão e logs seguros |
| BI | Fórmula, grão, linhagem, zero/NULL, frescor e revisão visual |

Nunca colar token, senha, chave privada, .env ou segredo em issue/PR. Segredo exposto deve ser rotacionado. Mudanças de produção/acesso seguem aprovação da equipe.
