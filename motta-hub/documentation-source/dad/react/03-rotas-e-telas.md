# 03 — Rotas e Telas

## Rotas públicas

| Caminho | Tela | Observação |
|---|---|---|
| `/` | Login | Entrada padrão da aplicação |
| `/login` | Login | Mesmo formulário da rota raiz |
| `/passwordRecovery` | Recuperação de senha | Fluxo demonstrativo |
| `/newPassword` | Nova senha | Fluxo demonstrativo |

## Rotas autenticadas

| Caminho | Tela ou área | Grupo de navegação |
|---|---|---|
| `/overview` | Visão geral | Análise |
| `/home` | Início e métricas | Página principal |
| `/users/*` | Administração de usuários | Usuários e permissões |
| `/usageHistory` | Histórico de uso | Análise |
| `/expiringProducts` | Alertas de vencimento | Análise |
| `/products` | Lista de produtos | Produtos |
| `/products/:productId` | Detalhes do produto | Produtos |
| `/productsRegistration` | Cadastro e importação demonstrativa | Produtos |
| `/stock` | Estoque e inventário | Estoque |
| `/stock/cash-closing/:discrepancyId` | Detalhe de divergência de caixa | Estoque/relatório |
| `/stock/counts/new` | Nova contagem | Estoque |
| `/stock/damages` | Avarias e consumo interno | Estoque |
| `/stock/transfers` | Transferências de lojas | Estoque |
| `/stock/transfers/new` | Nova transferência | Estoque |
| `/stock/suppliers` | Fornecedores | Estoque |
| `/stock/suppliers/new` | Cadastro de fornecedor | Estoque |
| `/managementReports` | Relatórios gerenciais e exportação | Relatórios |
| `/accounting/sped` | Relatório financeiro mensal | Contabilidade |
| `/account` | Minha conta | Conta |

O caminho `/users/*` entrega os subcaminhos ao módulo `Users`. A lista de rotas usada pela auditoria de navegação inclui, por exemplo, `/users/new` e `/users/audit`.

## Proteção e rota inexistente

`PrivateRoute` envolve o layout principal e redireciona quem não está autenticado para `/login`. As rotas `/` e `/login` apresentam a mesma tela. Caminhos que não correspondem às rotas declaradas caem em `ErrorPage`, que oferece a ação “Voltar para o início”.

## Navegação persistente

`MainLayout` reúne os elementos comuns das telas administrativas. A barra lateral abre as áreas principais; `FolderNavigation` organiza subáreas de análise, estoque, contabilidade e usuários. No modo compacto, o menu lateral usa um botão com `aria-expanded` e `aria-controls`, e pode ser fechado pelo teclado com `Escape`.

## Fonte da lista

Esta tabela reflete `src/routes/index.tsx`, `src/config/folder-navigation.ts` e `scripts/lighthouse-routes.cjs`. Para mudar a navegação, atualize a implementação e mantenha esta referência alinhada às rotas existentes.

---

*Anterior: [02 — Arquitetura do Front-end](02-arquitetura.md) · Próximo: [04 — Dados, Serviços e Autenticação](04-dados-servicos-autenticacao.md).*
