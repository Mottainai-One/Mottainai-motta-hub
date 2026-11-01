# 01 — Visão Geral e Áreas Funcionais

## Papel do front-end

O Sistema Mottainai neste projeto é uma aplicação administrativa web feita com React, TypeScript e Vite. Sua interface organiza telas para acompanhamento de produtos, estoque, usuários e relatórios. O README do projeto descreve esse recorte como front-end administrativo; não há aqui um servidor de aplicação ou uma integração de dados real.

O propósito de produto associado ao Mottainai é apoiar a gestão de estoque e a redução do desperdício. Esta aplicação representa parte desse contexto por meio de painéis, cadastros, alertas e fluxos operacionais demonstrativos.

## Áreas observadas na interface

| Área | O que a interface apresenta | Rotas principais |
|---|---|---|
| Indicadores e acompanhamento | Visão geral, métricas, ranking, histórico de uso e alertas de vencimento | `/overview`, `/home`, `/usageHistory`, `/expiringProducts` |
| Produtos | Lista, detalhes, cadastro individual e importação demonstrativa | `/products`, `/products/:productId`, `/productsRegistration` |
| Estoque | Inventário, contagem, avarias/consumo interno e transferências | `/stock`, `/stock/counts/new`, `/stock/damages`, `/stock/transfers` |
| Fornecedores | Lista e formulário de cadastro | `/stock/suppliers`, `/stock/suppliers/new` |
| Usuários | Administração de funcionários, permissões e tela de auditoria | `/users/*` |
| Relatórios e contabilidade | Relatórios gerenciais, exportação e relatório financeiro mensal | `/managementReports`, `/accounting/sped`, `/stock/cash-closing/:discrepancyId` |
| Acesso e conta | Login, recuperação e redefinição demonstrativas, além da tela de conta | `/login`, `/passwordRecovery`, `/newPassword`, `/account` |

Os nomes descrevem telas e rotas do front-end. Eles não garantem que exista uma operação equivalente no servidor ou que os registros sejam persistidos de forma centralizada.

## Limites funcionais atuais

- O README raiz informa que não existe integração com API de autenticação ou de dados.
- Os exemplos operacionais em `src/data/` são registros locais de demonstração.
- Serviços de algumas jornadas simulam espera e resultado no navegador, sem enviar requisição HTTP.
- Relatórios salvos e preferências usam armazenamento local do navegador; por isso não formam uma base compartilhada entre pessoas ou dispositivos.
- A tela `/accounting/sped` gera um relatório demonstrativo a partir de divergências de caixa. O código explicita que os dados são uma amostra, sem ano informado, e que a soma não deve ser interpretada automaticamente como perda, prejuízo, receita ou saldo.

## Mapa de áreas

```text
Interface administrativa
├── Indicadores, uso e vencimentos
├── Produtos e fornecedores
├── Estoque, contagens, avarias e transferências
├── Usuários e permissões
├── Relatórios gerenciais e relatório financeiro demonstrativo
└── Acesso, conta e preferências de acessibilidade
```

## Referências no código

- Rotas e telas: `src/routes/index.tsx`
- Navegação lateral: `src/components/Sidebar/index.tsx`
- Grupos de navegação: `src/config/folder-navigation.ts`
- Dados demonstrativos: `src/data/`
- Estado de autenticação: `src/context/AuthProvider.tsx`
- Contexto de integração: `README.md`

---

*Próximo: [02 — Arquitetura do Front-end](02-arquitetura.md).*
