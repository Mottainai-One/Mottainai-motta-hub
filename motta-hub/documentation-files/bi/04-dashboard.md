# Dashboard e experiência de uso

## Contrato de consumo

O dashboard publicado mantém o objeto Databricks de ID
`01f1d22904b81b738aef457d6a67f354` e usa o SQL Warehouse de ID
`64bc14de5692c645`, conforme o bundle BI consultado. A página publicada pode
ser aberta em:

[Dashboard Mottainai — Databricks](https://dbc-38ac8920-cbf4.cloud.databricks.com/sql/dashboardsv3/01f1d22904b81b738aef457d6a67f354?o=7474654317437663)

O dashboard deve consultar exclusivamente `motta_analytics.gold`. A definição
versionada e as consultas dos datasets vivem no repositório
[Mottainai-BI](https://github.com/Mottainai-One/Mottainai-BI). Ao atualizar,
preservar o mesmo ID quando a intenção for atualizar o painel existente, revisar
permissões e publicar a versão nova somente após o job Gold passar.

## Páginas

| Página | Conteúdo principal | Fontes Gold |
|---|---|---|
| Visão executiva | Receita, vendas concluídas, ticket, comparação temporal, evolução diária, receita por loja/produto, frescor | `sales_daily`, `sales_tickets`, `product_sales_daily`, `dashboard_freshness` |
| Comercial | Cobertura de lojas/produtos, unidades vendidas, receita por produto, métodos e valores de pagamento | `sales_daily`, `product_sales_daily`, `payment_mix` |
| Estoque | Unidades disponíveis, valor a custo, alertas de mínimo, lotes vencidos/a vencer e custo ausente | `inventory_health`, `inventory_batches` |
| Operações e perdas | Contagens, divergência, transferências, reposição, doações, descartes e ciclo de alertas | `inventory_count_accuracy`, `transfer_execution`, `replenishment_fulfillment`, `product_destinations`, `alert_action_funnel` |
| Distribuição e qualidade | Histograma/boxplot de tickets, qualidade Silver e limites da amostra | `sales_tickets`, `quality_summary` |
| Dados e KPIs | Fórmulas, análises, fontes, estado de publicação e datasets usados pelos cartões | `ds_kpi_dictionary`, `ds_reliability` e datasets por domínio |

Em 30/10/2026, o contrato de dashboard registrava 14 datasets e seis páginas
canvas. Confirme o objeto publicado antes de tratar essa contagem como estado
atual.

## Aba Data e datasets

A aba Data deve permitir que o analista inspecione as linhas por trás dos
indicadores sem abrir o banco transacional. O contrato documentado inclui:

- `ds_period`, `ds_inventory`, `ds_payment`: vendas, fotografia de estoque e
  pagamentos;
- `ds_operations`, `ds_counts`, `ds_destinations`: operações, inventário
  contado e destinação;
- `ds_reliability`: lote, frescor e validações;
- `ds_kpi_dictionary`: catálogo semântico com fórmula, interpretação, fonte e
  situação do KPI.

Os datasets de detalhes devem usar o mesmo corte/batch dos cartões. A página de
dados não deve exibir números fictícios ou preencher vazios com zero só para
construir visualizações.

## Filtros e semântica

- **Período:** filtra métricas de venda e eventos com data no intervalo.
- **Loja:** filtra vendas e operações da loja; em transferências, a dimensão de
  origem/destino deve estar identificada para que o recorte não seja ambíguo.
- **Estoque:** representa o snapshot válido mais recente. O filtro de data de
  venda não deve mudar essa fotografia; use o corte do snapshot no rótulo.
- **Comparação temporal:** comparar janelas de duração equivalente e indicar
  período parcial. Quando o denominador do período anterior é zero, mostrar
  “sem base de comparação”, não infinito.
- **Mapa:** não publicar até existir latitude/longitude confiável e cobertura
  suficiente. A consulta opcional que retorna zero pontos não é evidência de um
  mapa pronto para decisão.

## Regras de comunicação visual

1. **Contexto no cartão:** nome do KPI, unidade, período/filtro ativo e uma frase
   que explique o significado do resultado.
2. **Variação com referência:** exibir período base e direção; não atribuir
   causalidade ao aumento ou queda.
3. **Estado legível:** distinguir zero, sem dado, falha de atualização e dado
   desatualizado com texto explícito, não somente cor.
4. **Semântica consistente:** receita, valor a custo, unidade, taxa e contagem
   não devem compartilhar formatação ou rótulos ambíguos.
5. **Amostra exposta:** mostrar tamanho da população, intervalo e número de
   lojas/produtos quando isso afetar interpretação.
6. **Tabelas acionáveis:** ordenar por severidade/valor relevante, apresentar
   rótulo textual e não depender apenas de cor para sinalizar risco.
7. **Filtro controlável:** manter filtros visíveis, permitir identificar o
   recorte aplicado e fornecer forma clara de redefini-lo.
8. **Responsividade e acessibilidade:** testar contraste, leitura, foco de
   teclado, rótulos e comportamento em telas menores no dashboard publicado.

## Referência de UX do primeiro ano

As análises heurísticas de CRUD e Landing compartilhadas pela equipe reforçam
princípios de visibilidade do estado, correspondência com a linguagem do
usuário, controle, consistência, reconhecimento, prevenção de erros e ajuda.
Esses princípios foram convertidos na lista acima como critérios para revisar o
BI. As análises originais tratam de telas administrativas e do site, não do
dashboard; não se deve afirmar que o dashboard passou por aquelas entrevistas.

## Aceite funcional e visual

Antes de encerrar uma alteração de dashboard:

- executar todas as consultas/datasets afetados no SQL Warehouse;
- verificar que os datasets usam tabelas Gold e lote coerente;
- conferir valores em consulta independente e regras de conciliação;
- abrir a versão publicada e revisar cada página, cartão e tabela;
- alterar e limpar filtros de período e loja;
- verificar como aparecem `NULL`, zero, erro e falta de atualização;
- conferir títulos, unidades, análise junto a KPIs, formatação monetária e
  responsividade;
- pedir revisão de outra pessoa da equipe para semântica e leitura executiva;
- registrar evidência de execução e aceite no PR de BI.

A definição SQL bem-sucedida não substitui inspeção visual manual. O projeto
registrou essa inspeção como pendente na evidência de 30/10/2026.
