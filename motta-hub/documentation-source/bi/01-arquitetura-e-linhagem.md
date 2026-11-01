# Arquitetura e linhagem de dados

## Sistemas e responsabilidades

| Componente | Responsabilidade | Padrão de escrita/leitura |
|---|---|---|
| Legado | Sistema de origem anterior | Não é fonte direta do dashboard |
| PostgreSQL `MOTTAINAI` | Estado transacional atual do produto | APIs e integrações escrevem; o RPA analítico lê |
| PostgreSQL `MOTTAINAI_ANALITICO` | Publicação histórica e orientada a consulta | RPA publica; Databricks lê |
| Unity Catalog `motta_analytics` | Camadas Delta, controle, governança e semântica do BI | Pipeline Databricks escreve; dashboard consome Gold |

Os dois bancos PostgreSQL são databases independentes, mesmo quando hospedados
na mesma instância Aiven. Não existem chaves estrangeiras nem joins SQL entre
databases físicos. A relação entre os bancos é feita por um processo de carga,
com identificadores e contratos de dados preservados.

## Fluxos e cadência

### Legado para operacional

É uma integração operacional separada da matéria de BI. O workflow
`legacy-to-operational.yml` no snapshot local revisado usa `*/30 * * * *`.
A equipe havia solicitado cinco minutos; portanto a documentação registra essa
divergência como pendência de confirmação, sem presumir que o ajuste já esteja
implantado. O intervalo ativo deve ser lido no workflow mesclado do GitHub
Actions.

### Operacional para analítico

O workflow `operational-to-analytics.yml` define execução diária às 02:00 em
`America/Sao_Paulo`, além de execução manual. A RPA lê `MOTTAINAI` e publica no
database separado `MOTTAINAI_ANALITICO`, schema `mottainai_analytics`. O job de
BI não substitui essa carga.

O contrato de publicação usado pelo Databricks identifica uma execução válida
em `mottainai_analytics.job_log` por:

- `job_name = 'operational_to_analytics_daily'`;
- `status = 'SUCCEEDED'`;
- `batch_id` e `cutoff_at` preenchidos;
- `metadata ->> 'publication_contract' = 'analytics_mart_v1'`.

O Databricks seleciona a publicação válida mais recente, incluindo o corte da
origem e o horário de publicação. A presença de uma tabela ou de um batch
antigo, sem esse contrato, não comprova que a fotografia necessária foi
publicada.

### Analítico para Databricks

O bundle BI (`mottainai_bi`) define o job `mottainai-analytics-to-medallion`,
com horário previsto 02:30 em `America/Sao_Paulo` e no máximo uma execução
simultânea. As tarefas dependem nesta ordem:

```text
preflight → bronze → silver → gold → refresh_dashboard
```

O preflight testa as conexões dos dois PostgreSQL, verifica o database alcançado,
consulta um objeto operacional para validar conectividade e busca o lote
analítico com o contrato esperado. A conexão operacional é apenas de validação;
os dados que alimentam Bronze, Silver, Gold e o dashboard vêm do analítico.

## Contratos e escopo da cópia

A carga RPA é um contrato de dados selecionado, não uma garantia de que todas as
tabelas, colunas e exclusões físicas do operacional estejam replicadas. Os
datasets definidos no carregador RPA incluem dimensões de empresa, loja,
categoria, produto, funcionário e cliente, além de fatos de venda, pagamento,
movimento e snapshot de estoque, contagem de inventário, alertas, ações,
transferências, reposição, doações, descartes e resumo diário de loja.

O Databricks copia uma seleção própria para Bronze. No código BI revisto, essa
seleção abrange quatro dimensões (`dim_company`, `dim_store`, `dim_category`,
`dim_product`), fatos transacionais e operacionais e sete objetos publicados do
analítico usados para reconciliação. As dimensões de funcionário e cliente não
são copiadas para a Bronze do dashboard nessa seleção. Consulte a lista
`relations` em `notebooks/00_bronze_analitico.py` e os `Dataset` em
`analytics/load.py` como contratos executáveis; não derive escopo somente do
nome de uma view antiga.

Campos preenchidos com constantes ou valores padrão exigem atenção. Na versão
de carga analisada, por exemplo, desconto de venda/item e quantidade reservada
não são inferidos a partir de fontes inexistentes; o custo/estoque e indicadores
relacionados devem seguir os limites do [catálogo de KPIs](03-catalogo-de-kpis.md).

## Idempotência, consistência e publicação

- O RPA abre e reconcilia uma execução identificada por `batch_id`, registra
  contagens e publica o lote apenas depois das etapas de staging e validação.
- A Bronze preserva os dados no grão da origem e associa as linhas ao batch e
  aos metadados do corte/publicação.
- Repetição da mesma publicação não deve criar um segundo lote visível. Se um
  batch já existe, mas uma relação esperada está ausente, a Bronze pode
  reprocessar a fotografia para completar as tabelas necessárias.
- Silver valida e registra resultados antes de liberar o lote seguinte.
- Gold não deve avançar quando as validações impeditivas ou a reconciliação
  financeira falharem; a publicação anterior precisa continuar consultável.
- O refresh do dashboard é a última tarefa do job. Ele não representa uma nova
  ingestão operacional.

## Conexões e credenciais

As conexões Unity Catalog documentadas no bundle são
`conection_motta_operacional` (database `MOTTAINAI`) e `motta_analytics`
(database `MOTTAINAI_ANALITICO`). Elas não devem ser confundidas com o catálogo
de destino de mesmo nome `motta_analytics`. Senhas, tokens, chaves e certificados
privados não pertencem a notebooks, consultas, JSON do dashboard ou esta
documentação. Administradores devem manter segredos em mecanismos próprios do
Databricks/Aiven/GitHub conforme a responsabilidade de cada fluxo e limitar a
permissão às identidades que executam a carga.

## Regra de consumo

```text
dashboard → motta_analytics.gold → motta_analytics.silver/bronze
```

Consultas de dashboard não devem apontar diretamente para tabelas Bronze,
views operacionais no PostgreSQL, schemas de staging, ou banco operacional. A
exceção é uma consulta de diagnóstico controlada fora da camada de apresentação.
