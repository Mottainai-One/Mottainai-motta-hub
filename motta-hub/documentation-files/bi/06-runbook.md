# Runbook operacional — BI Databricks

## Frequência e ordem esperada

| Horário/frequência | Processo | Observação |
|---|---|---|
| Conforme workflow legado ativo | Legado → `MOTTAINAI` | No snapshot local revisto, o cron ainda está em 30 minutos; meta de cinco minutos requer verificação do deploy |
| Diariamente, 02:00 BRT | `MOTTAINAI` → `MOTTAINAI_ANALITICO` | GitHub Actions `operational-to-analytics.yml`; admite execução manual |
| Diariamente, 02:30 BRT | Job `mottainai-analytics-to-medallion` | Preflight → Bronze → Silver → Gold → refresh dashboard |

Horários do job são uma configuração versionada. Antes da operação manual,
verifique o workflow e a próxima execução no GitHub Actions/Databricks. A
execução Databricks deve ocorrer depois que o lote esperado for publicado. A
fonte canônica do lote BI atual é a publicação no `job_log` com
`publication_contract = analytics_mart_v1`.

## Acessos e configuração

O bundle Databricks tem perfil documentado `mottainai-bi`; conexões Unity Catalog
`conection_motta_operacional` e `motta_analytics`; catálogo de destino
`motta_analytics`; dashboard ID `01f1d22904b81b738aef457d6a67f354`; warehouse ID
`64bc14de5692c645`. IDs não substituem permissões nem garantem que o recurso
continue ativo.

Com CLI oficial já instalado e perfil autenticado, validar e implantar a partir
do repositório `Mottainai-BI` (não do Hub):

```powershell
databricks auth describe --profile mottainai-bi
databricks bundle validate --profile mottainai-bi
databricks bundle deploy --profile mottainai-bi
```

Para uma execução manual, primeiro confirme a publicação analítica e depois
inicie o job existente:

```powershell
databricks jobs get 731348243647869 --profile mottainai-bi
databricks jobs run-now 731348243647869 --profile mottainai-bi
```

Não executar `bundle deploy` para diagnosticar somente a atualização de dados.
O deploy altera recursos; reexecução de job e deploy são operações diferentes.

## Conferência do lote no PostgreSQL

Conecte-se especificamente ao database `MOTTAINAI_ANALITICO` e rode:

```sql
SELECT job_id,
       job_name,
       status,
       started_at,
       finished_at,
       cutoff_at,
       batch_id,
       metadata ->> 'publication_contract' AS publication_contract,
       rows_read,
       rows_written,
       error_message
FROM mottainai_analytics.job_log
WHERE job_name = 'operational_to_analytics_daily'
ORDER BY job_id DESC
LIMIT 10;
```

O candidato do Databricks deve ser o registro mais recente com `SUCCEEDED`,
`batch_id`, `cutoff_at` e contrato `analytics_mart_v1`. Um `SUCCEEDED` de uma
versão antiga sem esses campos não satisfaz o preflight da versão atual.

Não escrever `MOTTAINAI_ANALITICO.mottainai_analytics.objeto` em PostgreSQL:
isso é referência cross-database e não é suportada. Se a conexão está no
database certo, consulte `mottainai_analytics.objeto`.

## Conferência no Databricks SQL

Use o SQL Warehouse com o catálogo `motta_analytics`:

```sql
SELECT * FROM motta_analytics.control.bronze_publication;
SELECT * FROM motta_analytics.control.silver_publication;
SELECT * FROM motta_analytics.control.publication;
SELECT * FROM motta_analytics.gold.dashboard_freshness;
SELECT * FROM motta_analytics.gold.quality_summary;

SELECT COUNT(*) AS completed_sales
FROM motta_analytics.gold.sales_tickets;

SELECT SUM(revenue_brl) AS revenue_brl
FROM motta_analytics.gold.sales_daily;

SELECT payment_method, SUM(paid_amount) AS paid_amount
FROM motta_analytics.gold.payment_mix
GROUP BY payment_method;

SELECT SUM(available_quantity) AS available_units,
       SUM(stock_value) AS stock_value_at_cost
FROM motta_analytics.gold.inventory_health;
```

Compare `batch_id` e horário do corte nos marcadores de controle e em
`dashboard_freshness`. Para conferir fatos operacionais, use também
`inventory_count_accuracy`, `transfer_execution`,
`replenishment_fulfillment`, `product_destinations` e `alert_action_funnel`.
Um resultado vazio pode significar ausência de eventos; valide as contagens da
origem e os relatórios Silver antes de abrir defeito.

## Diagnóstico por sintoma

| Sintoma | Verificações | Resposta segura |
|---|---|---|
| Preflight não encontra batch | Job RPA mais recente; status, contrato, `batch_id`, `cutoff_at` | Não avançar camadas; corrigir/publicar a carga e executar o job após o lote válido |
| Conexão alcança database errado | Perfil de conexão e `current_database()` | Corrigir conexão Unity Catalog. Não trocar apenas o nome do catálogo |
| Relação faltando na Bronze | Contrato de origem e lista `relations` do notebook | Corrigir schema/contrato e reprocessar; não criar tabela vazia para fazer o job passar |
| Regra Silver falha | `quality_results`, regra, contagem e amostra segura | Corrigir origem ou transformação; documentar exceção; preservar a publicação anterior |
| Gold não reconcilia | Totais por venda de vendas, itens e pagamentos; batch comum | Bloquear publicação até encontrar diferença ou documentar ajuste aprovado |
| Dashboard desatualizado/vazio | Batch em Gold, execução `refresh_dashboard`, filtros e permissões | Confirmar se o lote novo foi publicado e executar refresh após Gold |
| KPI aparece zero | população, período, denominador, lote e fonte | Distinguir zero real de sem base; usar `NULL` quando não há população válida |
| Dados parecem em tempo real | `source_cutoff_at`, frequência RPA e horário Databricks | Comunicar idade da fotografia; não ler operacional direto para contornar atraso |

## Reexecução e recuperação

1. Guardar o `batch_id`, IDs de execução e mensagens de erro.
2. Determinar se a falha aconteceu no RPA, Bronze, Silver, Gold ou refresh.
3. Corrigir a causa na fonte ou no repositório proprietário.
4. Se necessário, publicar novamente a carga RPA; não editar tabelas produtivas
   manualmente para fabricar uma publicação.
5. Confirmar a publicação válida no `job_log`.
6. Reexecutar o job Databricks, que deve processar o batch de forma idempotente.
7. Conferir marcadores e reconciliações em cada camada e os datasets do painel.
8. Registrar a causa, a resolução e qualquer alteração de KPI no PR/runbook.

Não excluir manualmente linhas de controle, batches ou Gold para contornar uma
falha. A recuperação deve preservar o último lote íntegro para consumidores.

## Escalonamento

- falha no fluxo legado → operacional: equipe responsável pela RPA de integração;
- falha na publicação operacional → analítico: responsável pelo repositório
  `Mottanai-RPA` e pelo contrato do banco;
- falha Bronze/Silver/Gold/dashboard: responsável pelo repositório
  `Mottainai-BI` e workspace Databricks;
- erro semântico/fórmula: responsável pelo KPI e revisor de negócio;
- possível exposição de dado pessoal ou segredo: interromper publicação, limitar
  acesso e acionar responsável por segurança/privacidade.
