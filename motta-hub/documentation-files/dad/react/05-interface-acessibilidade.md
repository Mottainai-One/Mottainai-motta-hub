# 05 — Interface, Responsividade e Acessibilidade

## Recursos presentes

O documento registra recursos observáveis na implementação; a presença de um recurso isolado não comprova conformidade completa com WCAG 2.1 AA.

| Recurso | Evidência no projeto | Finalidade |
|---|---|---|
| Idioma da página | `index.html` define `lang="pt-BR"` | Informa o idioma principal a leitores de tela e navegadores |
| Link para conteúdo principal | `MainLayout` oferece “Pular para o conteúdo principal” | Evita repetir a navegação ao percorrer páginas por teclado |
| Controles semânticos | Menu, ações e formulários usam elementos HTML de botão, link e campo | Mantém nome e comportamento nativos dos controles |
| Rótulos e erros de formulário | Login associa `label` e campo; erros usam `aria-invalid`, descrição e `role="alert"` | Ajuda a identificar campos e entender como corrigir uma entrada |
| Menu compacto | `Sidebar` informa expansão e controle; fecha com `Escape` e devolve foco ao botão | Torna o menu navegável sem depender de mouse |
| Preferências de leitura | Painel permite ajustar tema, contraste, tamanho e fonte, entre outras opções | Adapta a apresentação às preferências da pessoa usuária |
| Leitura em voz alta | `speechService` usa a API de síntese de fala do navegador, quando disponível | Oferece leitura de texto e controles de pausa, retomada e velocidade |
| Foco visível e movimento | CSS global e módulos contêm regras de foco e adaptação de movimento | Ajuda a localizar controles e respeita preferência de movimento reduzido |

## Tema e contraste

As preferências incluem temas claro, escuro e do sistema, além dos modos de contraste normal, alto e baixo. O README raiz esclarece que “Contraste baixo” reduz deliberadamente o contraste e não é um modo conforme WCAG AA. Para avaliação do contraste mínimo, considere o tema padrão ou alto e verifique as combinações efetivamente exibidas.

## Responsividade

Os componentes e páginas mantêm estilos em CSS Modules, com regras de mídia em vários módulos de layout, filtros, formulários e navegação. O menu lateral possui um modo compacto e os estilos organizam conteúdo em telas menores. Esta documentação identifica os mecanismos presentes; não registra uma validação manual completa em larguras específicas de celular, tablet e desktop.

## Limite de conformidade

Não foi feita nesta entrega uma auditoria integral de todos os critérios WCAG 2.1 A e AA, combinações de cores, leitores de tela, zoom ou cada fluxo de teclado. Portanto, não se declara conformidade WCAG AA do produto. A opção “Contraste baixo” é uma exceção já identificada no README raiz.

## Referências

- `index.html`
- `src/components/MainLayout/index.tsx`
- `src/components/Sidebar/index.tsx`
- `src/pages/Login/index.tsx`
- `src/components/FloatingButton/`
- `src/services/speechService.ts`
- `src/styles/accessibility.css` e arquivos `style.module.css` de componentes e páginas
- `src/utils/accessibilityPreferences.ts` e `src/utils/accessibilityColorContrast.ts`

---

*Próximo: [06 — Operação e Qualidade](06-operacao-qualidade.md).*
