# 01 — Visão Geral e Mapa de Domínios

## Missão e valor central

O Mottainai existe para combater o **desperdício de alimentos** no varejo. Sua proposta de valor se apoia em três pilares:

1. **Prever** — cruzar estoque, gôndola e fluxo de saída para antecipar **rupturas** e **vencimentos**.
2. **Agir** — sugerir, com aprovação do gerente, ações táticas (promoções, transferências, doações, descartes).
3. **Demonstrar impacto** — quantificar lucro salvo, produtos salvos, CO₂ evitado e economia consciente.

Isso é materializado por um **motor de inteligência de shelf life** (o *"cérebro"* do sistema) que observa o estoque em ciclo contínuo e emite diagnósticos e sugestões.

## Regras de negócio centrais

São as regras que estruturam quase todo o modelo de dados:

- **FEFO (First-Expire-First-Out):** toda saída de estoque prioriza o lote que vence primeiro.
- **Custo médio ponderado:** cada nova nota fiscal recalcula o custo médio do produto e sugere novo preço de venda.
- **Aprovação remota:** ações críticas (promoções, cancelamentos de caixa) dependem de aprovação do gerente.
- **Multitenancy por empresa:** cada empresa (locatária SaaS) é isolada das demais, com suas lojas e operações.
- **Rastreabilidade total:** toda ação relevante gera auditoria, histórico e trilha observável.

## As quatro superfícies e seus domínios

| Superfície | Domínios que mais consome |
|---|---|
| **Site Administrativo** | Catálogo, Escopo financeiro/gerencial, Relatórios, Regras, Controle de acesso |
| **App Administrativo** | Estoque, Reposição, Inteligência, Suprimentos |
| **App Cliente** | Cliente, Fidelidade, Promoção, Geolocalização, Impacto |
| **PDV (Caixa)** | Venda, Frente de caixa, Fidelidade |

## Mapa de domínios (blocos do negócio)

Os domínios abaixo agrupam os conceitos de negócio. Cada domínio se conecta aos demais como descrito no diagrama de entidades (`02-entidades-e-relacionamentos.md`).

```
┌────────────────────────────────────────────────────────────────────┐
│                       NÚCLEO MULTITENANT (SaaS)                    │
│   Plano · Empresa · Loja · Funcionário · Usuário · Papel/Acesso    │
└────────────────────────────────────────────────────────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
┌───────┴────────┐    ┌─────────┴─────────┐    ┌────────┴─────────┐
│   CATÁLOGO     │    │     ESTOQUE       │    │    VENDAS / PDV  │
│ Produto        │    │ Lote (validade)   │    │ Cliente          │
│ Categoria      │    │ Estoque por loja  │    │ Terminal/QR      │
│ Perfil Fiscal  │    │ Movimentação      │    │ Turno/Contagem   │
│ Fornecedor     │    │ Reposição         │    │ Venda/Item/Pagto │
│ Compra/NF      │    │                  │    │ Documento Fiscal │
└────────────────┘    └──────────────────┘    └───┬───────────────┘
        │                       │                │
        ▼                       ▼                ▼
┌────────────────────────────────────────────────────────────────────┐
│   FIDELIDADE E CLIENTE   ·   PROMOÇÃO   ·   IMPACTO SOCIOAMBIENTAL │
└────────────────────────────────────────────────────────────────────┘
        │                       │
        ▼                       ▼
┌────────────────────────────────────────────────────────────────────┐
│                 INTELIGÊNCIA — MOTOR DE SHELF LIFE                 │
│  Alerta · Ação sugerida · Transferência · Doação · Avarias/Descarte│
│  IA (previsão, recomendação, feedback, execução) · Regras do motor │
└────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────────┐
│          OBSERVABILIDADE — Auditoria · Logs · Eventos · KPI        │
└────────────────────────────────────────────────────────────────────┘
```

## Lista de domínios

| # | Domínio | Conceitos centrais | Valor para o negócio |
|---|---|---|---|
| D1 | **Multitenancy / Cadastro** | Plano, Empresa, Loja, Funcionário, Usuário, Papel | Isolamento de locatários e controle de acesso |
| D2 | **Catálogo & Compras** | Produto, Categoria, Perfil Fiscal, Fornecedor, Pedido, Recebimento/NF | Base de itens e entrada de mercadorias |
| D3 | **Estoque** | Lote, Estoque, Movimentação, Reposição | Visão física e FEFO do inventário |
| D4 | **Vendas & PDV** | Cliente, Terminal, Turno, Venda, Item, Pagamento, Documento Fiscal | Receita e operação de caixa |
| D5 | **Fidelidade & Cliente** | Conta de pontos, Transação, Recompensa, Resgate, Geocerca | Engajamento e recorrência |
| D6 | **Promoções** | Promoção, Item promocional, Aprovação | Incentivo de saída próxima ao vencimento |
| D7 | **Inteligência — Motor** | Alerta, Ação sugerida, Ação executada, Diagnósticos, Regras | Núcleo preditivo do Mottainai |
| D8 | **Logística & Sustentabilidade** | Transferência, Doação, Avarias/Descarte interno | Redistribuição e redução de perda |
| D9 | **Observabilidade & Governança** | Auditoria, Logs, Eventos, Jobs, KPI em cache, Históricos | Rastreabilidade e monitoramento |
| D10 | **Análise & BI** | Indicadores, dashboards, previsões, impacto | Visão executiva e tomada de decisão |

---

*Próximo: [02 — Entidades e Relacionamentos](02-entidades-e-relacionamentos.md)*
