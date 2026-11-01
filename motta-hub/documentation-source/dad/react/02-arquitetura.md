# 02 — Arquitetura do Front-end

## Inicialização e composição

A aplicação inicia em `index.html`, que define `lang="pt-BR"`, o elemento raiz e o carregamento de `src/main.tsx`. O ponto de entrada importa os estilos globais, envolve as rotas com `AuthProvider` e monta a árvore React em `#root`.

```text
index.html
   └── src/main.tsx
       ├── estilos globais e de acessibilidade
       └── AuthProvider
           └── src/routes/index.tsx
               ├── BrowserRouter e rotas
               ├── PrivateRoute nas áreas autenticadas
               └── MainLayout nas páginas administrativas
```

## Organização por responsabilidade

| Pasta | Responsabilidade no projeto |
|---|---|
| `src/pages/` | Telas ligadas às rotas, cada uma com sua pasta e arquivo de entrada `index.tsx` |
| `src/components/` | Peças reutilizáveis da interface, como navegação, tabelas, filtros, gráficos, carregamento e modais |
| `src/context/` | Estado compartilhado de autenticação por `AuthProvider` e `AuthContext` |
| `src/hooks/` | Acesso tipado ao contexto e coordenação de dados de algumas áreas |
| `src/services/` | Operações isoladas; atualmente incluem simulações, armazenamento local e lógica de relatórios, sem chamadas HTTP no código de `src/` |
| `src/data/` | Registros de demonstração consumidos por telas e serviços |
| `src/types/` | Tipos TypeScript de domínio e de propriedades de interface |
| `src/utils/` | Validações, transformações de relatórios, preferências e funções de apoio |
| `src/config/` | Configuração declarativa da navegação por seção |
| `src/styles/` | CSS global e regras compartilhadas de acessibilidade |

Os estilos específicos ficam junto aos componentes e às páginas em arquivos CSS Modules (`style.module.css`).

## Navegação e carregamento de telas

`src/routes/index.tsx` usa React Router DOM. Cada página principal é carregada com `React.lazy` e renderizada dentro de `Suspense`, que mostra o componente `Spinner` enquanto o módulo está carregando. Isso separa o carregamento de páginas em módulos e preserva um feedback visual durante a transição.

As rotas privadas ficam sob `PrivateRoute`. A autenticação é lida por `useAuth`; quando ausente, a pessoa é redirecionada para `/login`. As áreas autenticadas usam `MainLayout`, que compõe a barra lateral, o cabeçalho, a navegação contextual e a região principal.

Uma rota curinga (`*`) mostra `ErrorPage`, com uma ação para voltar ao início.

## Estado compartilhado e local

- O estado de autenticação usa `useReducer` com ações discriminadas, disponibilizado via Context.
- O hook `useAuth` concentra o acesso tipado ao Context e avisa quando usado fora do Provider.
- Formulários mantêm estado local na própria página ou componente.
- Preferências de acessibilidade e alguns dados de relatórios são persistidos pelo navegador; isso não equivale a sincronização remota.
- Hooks como `useRanking` e `useHistoricalMetrics` coordenam carregamento de dados simulados e cancelamento quando a tela deixa de precisar deles.

## Tipagem e validação

Os tipos de entidades e de propriedades estão organizados em `src/types/`. Regras de validação específicas ficam em `src/utils/`, por exemplo para login, produtos, fornecedores, contagens e transferências. Páginas e componentes consomem essas funções para apresentar erros e controlar o envio dos formulários.

## Referências de implementação

- Entrada: `src/main.tsx`
- Rotas: `src/routes/index.tsx`
- Layout administrativo: `src/components/MainLayout/index.tsx`
- Autenticação compartilhada: `src/context/AuthProvider.tsx`, `src/context/AuthContext.tsx` e `src/hooks/useAuth.ts`
- Aliases e build: `vite.config.ts`, `tsconfig.app.json` e `package.json`

---

*Próximo: [03 — Rotas e Telas](03-rotas-e-telas.md).*
