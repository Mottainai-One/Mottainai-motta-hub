# 02 — Entidades e Relacionamentos (nível conceitual)

Este documento apresenta as **entidades** do Mottainai e como elas se relacionam, em linguagem de negócio e cardinalidades, sem detalhes de implementação física (chaves, tipos e colunas estão no [Modelo Lógico](../model-logico/README.md)).

## Diagrama de relacionamento (visão macro)

```
PLANO ──< EMPRESA ──< LOJA ──< FUNCIONÁRIO ── 1:1 ── USUÁRIO ──< SESSÃO
                  └──< PRODUTO
                     │          │         └── USUÁRIO ── PODE SER ── GERENTE/ESTOQUISTA/OPERADOR
                     │          └── TEM ── LOJA
                     │
                     ├──< LOJA ──< ENDEREÇO  (fornecedor também possui endereço)
                     └──< LOJA ──< INVENTÁRIO (por lote)

CATEGORIA ──< PRODUTO >── PERFIL FISCAL
FORNECEDOR >──< PRODUTO  (via associação “produtos de fornecedor”)
　　　　　　　　　 │
                └── PRODUTO ──< LOTE ──< ESTOQUE-POR-LOJA ──< MOVIMENTAÇÃO

PEDIDO DE COMPRA ──< ITEM DO PEDIDO ──< RECEBIMENTO ──< ITEM DE RECEBIMENTO ── GERERA ── LOTE

CLIENTE ──< LOYALTY/ACCOUNT ──< TRANSAÇÃO DE PONTOS
CLIENTE ──< GEOCERCA (lojas próximas)
CLIENTE ── OPCIONAL EM ── VENDA

TERMINAL ──< TURNO ──< VENDA
VENDA ──< ITEM DE VENDA  ──> LOTE (FEFO)
VENDA ──< PAGAMENTO
VENDA ──1:1── DOCUMENTO FISCAL (NF-e / NFC-e / SAT)
VENDA ──< SOLICITAÇÃO DE CANCELAMENTO  (requer aprovação do gerente)

ALERTA ──< AÇÃO SUGERIDA ──> pode gerar ──> PROMOÇÃO | TRANSFERÊNCIA | DOAÇÃO | DESCARTE

MODELO DE IA ──< PREVISÃO ──< RECOMENDAÇÃO ──< FEEDBACK
RECOMENDAÇÃO ──< EXECUÇÃO
VARREDURA DO MOTOR ──< SUGESTÃO DO MOTOR
REGRA DO SISTEMA  (motor / financeira / validade / preço)

AUDITORIA · LOGS · EVENTOS · JOBS · HISTÓRICOS · KPI  (camada transversal)
```

## Entidades e papéis

### 1. Núcleo multitenant (SaaS)

| Entidade | Papel no negócio |
|---|---|
| **Plano** | Tipo de assinatura SaaS oferecido à empresa |
| **Empresa** | Locatária do sistema; dona de uma ou mais lojas |
| **Loja (Unidade)** | Ponto de venda/filial da empresa; gerencia seu próprio estoque |
| **Funcionário** | Pessoa vinculada a uma loja, com papel (papel define o nível de acesso) |
| **Usuário** | Credencial de acesso de um funcionário (login/senha) |
| **Sessão de Funcionário** | Login por dispositivo com refresh token rotativo, expiração e revogação |
| **Papel (Cargo)** | Perfil com nível de permissão (Operador de caixa, Estoquista, Gerente, Dono) |
| **Endereço** | Localização reutilizada por loja, fornecedor e empresa; cliente usa token não reversível |

### 2. Catálogo & Fornecedores

| Entidade | Papel no negócio |
|---|---|
| **Produto (SKU)** | Item de uma empresa; SKU e código de barras são únicos dentro dessa empresa |
| **Categoria de Produto** | Agrupamento (mercearia, bebidas, carnes, …) |
| **Perfil Fiscal** | Regras tributárias (CFOP, ICMS, PIS, COFINS) do produto |
| **Fornecedor** | Origem das mercadorias |
| **Produto de Fornecedor** | Associação produto↔fornecedor (código, preço, lead time) |

### 3. Compras & Recebimento

| Entidade | Papel no negócio |
|---|---|
| **Pedido de Compra** | Solicitação de mercadoria a um fornecedor para uma loja |
| **Item do Pedido** | Produto, quantidade e preço de cada linha do pedido |
| **Recebimento** | Conferência da entrega do pedido |
| **Item de Recebimento** | Quantidade recebida por produto, com fabricação/validade; **gera um lote** |

### 4. Estoque

| Entidade | Papel no negócio |
|---|---|
| **Lote** | Unidade rastreável de produto com data de validade (base do FEFO) |
| **Estoque por Loja** | Quantidade atual de um lote em uma loja (normal/consignado/quarentena) |
| **Movimentação** | Todo evento de entrada/saída/ajuste do estoque |
| **Reposição (Pré-lista)** | Lista de abastecimento indicando quantidades a retirar da câmara-fria |

### 5. Vendas & PDV

| Entidade | Papel no negócio |
|---|---|
| **Cliente** | Consumidor final (modal) |
| **Terminal** | Equipamento de caixa de uma loja |
| **Turno (Shift)** | Abertura/fechamento do caixa com valor inicial e sangria |
| **Venda** | Transação comercial, com status (concluída/cancelada/devolvida) |
| **Item de Venda** | Produto e quantidade vendidos; seleciona lote FEFO automaticamente |
| **Pagamento** | Forma e valor (dinheiro, cartão, PIX, boleto) com parcelamento |
| **Documento Fiscal** | NF-e / NFC-e / SAT emitido para a venda |
| **Solicitação de Cancelamento** | Pedido de cancelamento de item/venda que exige aprovação remota |

### 6. Fidelidade & Promoção

| Entidade | Papel no negócio |
|---|---|
| **Conta de Fidelidade** | Acúmulo de pontos por cliente |
| **Transação de Pontos** | Ganho/resgate/ajuste/expiração de pontos |
| **Recompensa** | Prêmio resgatável por pontos |
| **Resgate** | Troca de pontos por recompensa |
| **Geocerca** | Raio de proximidade cliente↔loja para alertas de queima de estoque |
| **Promoção** | Oferta com tipo (percentual/valor fixo/preço especial) e aprovação gerencial |
| **Item Promocional** | Produto dentro de uma promoção |

### 7. Inteligência — Motor de Shelf Life

| Entidade | Papel no negócio |
|---|---|
| **Alerta** | Aviso de risco (vencimento, estoque crítico, ruptura, lentidão, excesso) |
| **Ação Sugerida** | Recomendação tática (promoção/transferência/doação/descarte/reposição) gerada a partir de um alerta |
| **Transferência** | Movimentação de mercadoria entre lojas (próxima do vencimento para filial com maior giro) |
| **Doação** | Redirecionamento de alimentos a instituições |
| **Avarias / Descarte interno** | Baixa de produtos avariados ou consumidos internamente |
| **Modelo de IA** | Modelo de previsão/recomendação/classificação |
| **Previsão** | Estimativa de demanda/ruptura por produto e loja |
| **Recomendação** | Ação sugerida pela IA, com feedback e execução |
| **Varredura do Motor** | Ciclo de observação (SKUs escaneados, diagnósticos, assertividade) |
| **Sugestão do Motor** | Tática concreta aceita/rejeitada/editada pelo operador |
| **Regra do Sistema** | Parâmetros configuráveis (motor, financeiro, validade, preço) |

### 8. Observabilidade & Análise

| Entidade | Papel no negócio |
|---|---|
| **Auditoria** | Trilha de inserções/atualizações/exclusões sensíveis |
| **Logs** | Registros de sistema, erros e integrações |
| **Evento** | Fila de eventos assíncronos |
| **Job** | Controle de execução de automações |
| **KPI em cache** | Indicadores pré-calculados (com expiração) para dashboards |
| **Históricos** | Mudanças de produto/fornecedor/preço ao longo do tempo |
| **Views analíticas** | Indicadores agregados (vendas, perdas, rupturas, sustentabilidade, IA) |

## Regras de cardinalidade resumidas

| Relação | Cardinalidade |
|---|---|
| Empresa → Loja | 1 : N |
| Loja → Funcionário | 1 : N |
| Funcionário → Usuário | 1 : 1 |
| Usuário → Sessão | 1 : 0..N |
| Empresa → Produto | 1 : N |
| Produto → Lote | 1 : N |
| Lote → Estoque-por-loja | 1 : N (por loja) |
| Estoque-por-loja → Movimentação | 1 : N |
| Venda → Item de Venda | 1 : N |
| Venda → Documento Fiscal | 1 : 1 |
| Fornecedor → Produto | N : M (via associação) |
| Alerta → Ação Sugerida | 1 : N |
| Ação Sugerida → (Promoção/Transferência/Doação/Descarte) | 1 : 0..1 |
| Cliente → Conta de Fidelidade | 1 : 1 |
| Cliente → Geocerca | 1 : N |
| Varredura do Motor → Sugestão | 1 : N |

---

*Próximo: [Modelo Lógico](../model-logico/README.md)*
