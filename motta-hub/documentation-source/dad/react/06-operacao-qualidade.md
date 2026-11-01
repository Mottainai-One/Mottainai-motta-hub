# 06 — Operação e Qualidade

## Pré-requisitos

- Node.js e npm instalados.
- O fluxo de CI configura Node.js 22; essa é a versão usada pela automação atual, não uma indicação de que outras versões foram validadas.

## Instalação e execução local

Na raiz do projeto:

```bash
npm ci
npm run dev
```

O primeiro comando instala as dependências do lockfile; o segundo inicia o servidor local do Vite.

## Comandos disponíveis

| Comando | Uso |
|---|---|
| `npm run build` | Executa a verificação TypeScript e gera o build de produção em `dist/` |
| `npm run preview` | Serve localmente o build já gerado |
| `npm run lint` | Executa ESLint |
| `npm test` | Executa testes Node.js e a suíte Vitest |
| `npm run test:node` | Executa apenas os testes com o test runner do Node.js |
| `npm run test:react` | Executa apenas Vitest com ambiente jsdom |
| `npm run lighthouse:ci` | Gera build especial de auditoria e percorre as rotas configuradas |

Os testes automatizados existentes estão em `tests/`. Esta documentação não executou comandos de teste ou build.

## Auditoria Lighthouse

`npm run lighthouse:ci` usa o modo `lighthouse`, que habilita a autenticação simulada para visitar páginas privadas. Esse artefato serve para auditoria local e não deve ser publicado como o build normal de produção. Os relatórios são escritos em `.lighthouseci/reports/`, diretório ignorado pelo controle de versão. `LIGHTHOUSE_AUTH_TOKEN` pode fornecer um token de teste; se omitido, o script cria um token local de demonstração.

## Integração contínua

O fluxo de integração contínua instala dependências, executa build, testes e lint. Ele também verifica a convenção de prefixos de commit configurada na automação. Outro fluxo constrói uma imagem de QA do front-end.

## Publicação

O README raiz não registra uma URL publicada de acesso. Por isso, esta documentação não inventa nem declara um endereço de deploy. Quando a publicação estiver definida, inclua o link no README raiz e confirme que ele aponta para o build normal, com autenticação real integrada antes de habilitar acesso a dados de produção.

## Arquivos de referência

- Scripts: `package.json`
- Build e alias de importação: `vite.config.ts`, `tsconfig.json` e `tsconfig.app.json`
- Testes: `tests/` e `vitest.config.ts`
- Rotas visitadas na auditoria: `scripts/lighthouse-routes.cjs`
- Arquivos de automação: `ci.yml` e `qa-container.yml`
- Contexto de deploy e integração: `README.md`

---

*Última atualização: 2026-10-29.*
