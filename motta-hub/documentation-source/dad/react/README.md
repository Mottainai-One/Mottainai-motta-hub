# Documentação do Front-end React — Sistema Mottainai

> Aplicação administrativa web · React 19 · TypeScript · Vite · fotografia do projeto em 2026-10-29

Este conjunto documenta o front-end que existe neste projeto. O sistema reúne telas administrativas para acompanhar produtos, estoque, usuários e relatórios. Os fluxos e dados descritos aqui são os encontrados no código; esta documentação não representa um contrato de API nem uma certificação de acessibilidade.

## Limite do escopo

O front-end ainda não está integrado a uma API de autenticação ou de dados. A autenticação é demonstrativa apenas em desenvolvimento e no build de auditoria Lighthouse. Registros de demonstração, preferências e relatórios podem ficar armazenados no navegador, conforme o fluxo. Esses dados não são compartilhados entre navegadores nem sincronizados com servidor.

O modelo e a operação do banco de dados pertencem à documentação de banco. Este guia descreve somente a aplicação React neste repositório.

## Navegação

| Documento | Conteúdo |
|---|---|
| [01 — Visão geral e áreas funcionais](01-visao-geral-e-areas.md) | Objetivo do front-end, escopo observado e áreas de uso |
| [02 — Arquitetura do front-end](02-arquitetura.md) | Inicialização, camadas, componentes compartilhados e fluxo de renderização |
| [03 — Rotas e telas](03-rotas-e-telas.md) | Rotas públicas, rotas protegidas e agrupamento de navegação |
| [04 — Dados, serviços e autenticação](04-dados-servicos-autenticacao.md) | Mocks, armazenamento local, validação e limites de integração |
| [05 — Interface, responsividade e acessibilidade](05-interface-acessibilidade.md) | Recursos presentes na interface e limites da verificação WCAG |
| [06 — Operação e qualidade](06-operacao-qualidade.md) | Instalação, comandos, build e automações de qualidade |

## Tecnologias principais

| Camada | Tecnologia observada |
|---|---|
| Interface | React 19 e TypeScript |
| Desenvolvimento e build | Vite 8 |
| Navegação | React Router DOM 7 |
| Gráficos | Chart.js 4 |
| Estado imutável | `useReducer`, React Context e `use-immer` em pontos do projeto |
| Verificações | ESLint, Node.js test runner, Vitest e Testing Library |

As versões acima vêm de `package.json` e são referências às dependências declaradas, não uma recomendação para atualizar versões.

## Como começar a leitura

1. Leia a [visão geral](01-visao-geral-e-areas.md) para entender as áreas que a interface apresenta.
2. Siga para a [arquitetura](02-arquitetura.md) e veja onde cada responsabilidade fica no código.
3. Consulte [rotas e telas](03-rotas-e-telas.md) para localizar os fluxos navegáveis.
4. Use o guia de [dados e autenticação](04-dados-servicos-autenticacao.md) antes de interpretar conteúdo demonstrativo como dado de produção.

---

*Última atualização: 2026-10-29 · Fonte: código presente neste projeto.*
