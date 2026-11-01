# Camadas medalhão no Databricks

## Objetivo do desenho

O medalhão separa ingestão, normalização/validação e consumo de negócio. A
camada Gold é a interface semântica dos painéis. Isso reduz a repetição de
regras em widgets e permite rastrear qual batch e qual conjunto de testes
originaram um KPI.

| Camada | Schema Unity Catalog | Propósito | Consumidores |
|---|---|---|---|
| Bronze | `motta_analytics.bronze` | Cópia Delta do contrato analítico publicado, próxima ao formato de origem, com batch e timestamps de linhagem | Silver e reconciliação |
| Silver | `motta_analytics.silver` | Tipos, nomes, status e datas normalizados; deduplicação/validação e resultados de qualidade | Gold |
| Gold | `motta_analytics.gold` | Fatos/marts e métricas de negócio estáveis, com grão e semântica explícitos | Dashboard e analistas autorizados |
| Controle | `motta_analytics.control` | Marcadores de publicação, batch processado e estado das camadas | Orquestração e runbook |

## Bronze

O notebook `00_bronze_analitico.py` confirma primeiro a publicação mais recente
com contrato `analytics_mart_v1`. Ele lê o database analítico através da conexão
Unity Catalog; não usa o operational database como fonte dos dados do painel.

O conjunto revisado contém as dimensões de empresa, loja, categoria e produto;
fatos de vendas, itens, pagamentos, fotografia de estoque, contagens,
transferências, reposição, doações, descartes, ciclo de alertas e ações; e
objetos analíticos de vendas, resumo mensal, estoque crítico, risco e visão
executiva usados para reconciliação. A lista autoritativa é o tuple `relations`
no notebook Bronze, porque ela pode evoluir independentemente deste resumo.

Cada linha carregada carrega metadados do lote, incluindo `_batch_id`,
`_source_cutoff_at` e `_source_published_at`. A ingestão verifica as relações
antes de gravar e compara contagens. Campos pessoais ou identificadores de
clientes/funcionários desnecessários ao dashboard devem ser minimizados já na
consulta Bronze, não somente escondidos na Gold.

## Silver

O notebook `01_silver.py` normaliza os dados para o modelo de análise. Exemplos
de regras:

- datas e horas convertidas para tipos de data/hora explícitos;
- quantidades e valores convertidos para decimais com precisão definida;
- nomes de status/tipo normalizados para comparações consistentes;
- chaves obrigatórias e relacionamentos verificados;
- duplicatas identificadas no grão declarado;
- quantidades não positivas, medidas ausentes e registros sem dimensão
  correspondente identificados conforme regra do fato;
- reconciliação entre venda, itens e pagamentos, na população elegível;
- publicação Silver vinculada ao batch e versão de regra.

Os registros inválidos não devem ser silenciosamente convertidos em valores
válidos. O resultado deve ser mensurável (linhas totais, linhas inválidas e
chaves duplicadas) e ter uma decisão explícita: rejeitar o lote, isolar a linha
ou aceitá-la com ressalva documentada. A configuração específica está no
notebook; qualquer exceção deve aparecer no catálogo e no runbook.

## Gold

O notebook `02_gold.py` publica marts orientados a decisão. O dashboard atual
consulta views Delta Gold como:

- `sales_daily`, `sales_tickets`, `product_sales_daily`;
- `payment_mix`;
- `inventory_health`, `inventory_batches`;
- `dashboard_freshness`, `quality_summary`;
- `inventory_count_accuracy`, `transfer_execution`;
- `replenishment_fulfillment`, `product_destinations`;
- `alert_action_funnel`.

As métricas devem ter grão, população e denominador estáveis. Por exemplo,
estoque é uma fotografia mais recente e não deve responder ao filtro de data das
vendas; taxa sem eventos elegíveis deve ser `NULL`, não 0%; receita de venda
concluída deve conciliar por venda com itens/pagamentos; e valor a custo não
deve ser descrito como perda realizada.

## Controle e publicação

O schema `motta_analytics.control` guarda o estado necessário para impedir que
um batch parcial seja servido como se estivesse completo. A sequência esperada
é:

1. preflight confirma fontes e batch;
2. Bronze registra a versão da publicação e todas as relações requeridas;
3. Silver termina transformação e regras de qualidade;
4. Gold materializa os marts para o batch válido;
5. os marcadores de publicação avançam somente no sucesso;
6. o dashboard é atualizado após Gold.

Na recuperação de falhas, preservar a última publicação íntegra é prioritário.
Não apagar tabelas ou marcadores manualmente para “destravar” um lote sem
registrar a causa e a estratégia de replay.

## Quando criar nova tabela ou KPI

Antes de criar objeto Gold, documentar:

1. pergunta de negócio e usuário responsável;
2. grão e chave única;
3. população e exclusões;
4. fórmula, unidade, janela e denominador;
5. fonte e dependências upstream;
6. testes de qualidade e reconciliação;
7. comportamento para nenhum evento, dado ausente e erro;
8. filtros que afetam o indicador;
9. classificação e retenção dos dados;
10. aceite visual e operacional do dashboard.

Uma view de PostgreSQL com nome `vw_*` não se torna automaticamente uma
camada Gold. Deve ser inspecionada, validada, trazida para Bronze/Silver e
reexpressa com semântica/documentação própria se for usada no dashboard.
