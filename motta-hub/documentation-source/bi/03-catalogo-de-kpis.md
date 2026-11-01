# Catálogo de KPIs do Mottainai BI

## Como interpretar este catálogo

“Disponível” significa que há fonte e definição para o cálculo; não garante que
o lote mais recente tenha eventos suficientes. “Condicional” significa que a
métrica só pode ser interpretada quando a janela, a população ou o histórico
forem adequados. “Pendente” significa que instrumentação, fonte ou método ainda
falta. O dashboard não deve transformar nulo em zero nem apresentar dados
ilustrativos como observações reais.

O contrato executável de referência está em
[`Mottainai-BI/docs/KPI_CATALOG.md`](https://github.com/Mottainai-One/Mottainai-BI/blob/main/docs/KPI_CATALOG.md).
Este documento resume o contrato de negócio para o Hub.

## Comercial

| Indicador | Definição recomendada | Unidade/grão | Estado e cautela |
|---|---|---|---|
| Receita líquida | Soma de `net_amount` de vendas concluídas (`COMPLETED`) | BRL; dia × loja | Disponível quando vendas estão conciliadas. Excluir canceladas e reembolsos conforme o contrato da origem |
| Vendas concluídas | Contagem distinta de vendas concluídas | Transações; dia × loja | Disponível. Não contar linhas de pagamento como venda |
| Ticket médio | Receita líquida ÷ vendas concluídas | BRL/venda; período × loja | `NULL` sem vendas; exibir população e período comparado |
| Itens por venda | Soma de `item_count` ÷ vendas concluídas | Itens/venda; período × loja | Diferente de unidades vendidas se uma linha incluir quantidade > 1 |
| Variação de receita | `(receita atual − receita comparação) ÷ receita comparação` | %; períodos equivalentes | `NULL` se período anterior for zero; não comparar período parcial a mês fechado sem aviso |
| Unidades vendidas | Soma de quantidades de itens elegíveis de vendas concluídas | Unidades; dia × produto × loja | Não inferir margem sem custo de venda compatível |
| Receita por produto/loja | Soma do subtotal dos itens elegíveis | BRL; produto × loja × período | Indicador de participação, não rentabilidade |
| Mix de pagamento | Soma de pagamentos conciliados por método | BRL e % do total; método × loja × período | Venda pode ser dividida em métodos; percentuais usam pagamentos conciliados e soma devem fechar com net sales |
| Lojas com vendas | Contagem distinta de lojas com venda concluída | Lojas; período | Cobertura, não taxa de conversão nem comparação justa sem normalização |

## Estoque

| Indicador | Definição recomendada | Unidade/grão | Estado e cautela |
|---|---|---|---|
| Unidades em mãos | Soma da quantidade na fotografia analítica publicada mais recente | Unidades; loja × produto × lote | Fotografia, não fluxo. Deve usar o corte da publicação |
| Unidades disponíveis | Em mãos menos reserva válida | Unidades; loja × produto | Na carga analisada, a reserva é preenchida com zero por falta de fonte; não chamar de disponibilidade real até corrigir o contrato |
| Valor do estoque | Quantidade em mãos × custo unitário médio válido | BRL a custo; loja × produto × lote | Não é receita, margem ou perda. Se custo faltar, valor agregado não deve tratar custo desconhecido como zero |
| Abaixo do mínimo | Disponível menor que o mínimo definido pela origem | Produtos/lojas e unidades; fotografia | Regra operacional. Usar nulo se mínimo não estiver definido |
| Unidades vencidas | Quantidade em lotes com validade anterior ao corte publicado | Unidades; fotografia | Exposição física; não prova descarte nem perda financeira |
| Unidades a vencer em 30 dias | Quantidade em lotes com validade entre o corte e corte + 30 dias | Unidades; fotografia | Horizonte de regra. Não chamar de previsão de perda |
| Valor de estoque a vencer | Quantidade elegível × custo válido | BRL a custo; fotografia | `NULL` ou incompleto quando custo ausente; não é perda realizada |
| Ruptura / stockout | Dias ou posições em que demanda elegível existiu e o estoque disponível era zero | Dias/loja/produto | Condicional: exige histórico de snapshots e medida de demanda; um snapshot atual não mede ruptura histórica |
| Giro de estoque | Custo das mercadorias vendidas no período ÷ estoque médio a custo | Índice por janela; produto × loja | Pendente até validar custo de venda, snapshots contínuos e janela suficiente |

## Operações, perdas e ações

| Indicador | Definição | Unidade | Limite de interpretação |
|---|---|---|---|
| Acuracidade das contagens | Posições concluídas com contagem = saldo do sistema ÷ posições concluídas elegíveis | %; loja × período | Não representa cobertura do inventário inteiro; excluir contagens abertas/canceladas |
| Divergência absoluta | Soma de `abs(contado − sistema)` nas posições elegíveis | Unidades; loja × período | Não somar diferenças líquidas, pois isso permite compensação entre excesso e falta |
| Valor da divergência | Divergência absoluta × custo válido por posição | BRL a custo | Pendente se custo faltar em qualquer posição da população declarada |
| Conclusão de transferências | Linhas/transferências concluídas ÷ elegíveis com itens | %; período × loja origem/destino | Não demonstra venda incremental nem redução de perda |
| Reposição observada | Quantidade executada ÷ quantidade sugerida em linhas com execução concluída | %; loja × período | Excluir planos não executados; não é taxa global de adoção |
| Doações | Quantidade/valor de itens com status e destino de doação confirmado | Unidades/BRL a custo | Reportar doação observada, não benefício social ou economia sem método adicional |
| Descartes | Quantidade/valor de itens descartados confirmados | Unidades/BRL a custo | Perda realizada somente se status, custo e população estiverem reconciliados |
| Resolução de alertas | Alertas resolvidos ÷ alertas registrados/elegíveis | %; tipo/prioridade/loja | Mede estado/fluxo, não precisão de alerta ou efetividade da ação |
| Precisão/recall de alertas | TP/(TP+FP) e TP/(TP+FN), com rótulo de resultado observado | %; modelo/janela | Pendente de resultado validado, rótulos e definição de falso positivo/negativo |
| Efetividade de transferência | Resultado posterior comparado a controle/linha de base | Métrica de negócio pré-definida | Pendente de desenho de comparação causal; execução concluída não prova efeito |

## IA, cliente e sustentabilidade

| KPI candidato | Pré-requisito de publicação responsável | Estado |
|---|---|---|
| Precisão e recall de previsão | Alvo observado, horizonte, janela de validação e baseline versionados | Pendente até haver previsões e resultados rotulados |
| Adoção de recomendação | Eventos de sugestão, visualização, aceitação, rejeição, execução e motivo ligados por ID | Pendente se esses eventos não estiverem carregados |
| Valor recuperado/economia atribuível | Resultado realizado, custo líquido, baseline comparável e método causal aceito | Não inferir de uma recomendação ou transferência |
| Recompra/fidelidade | Identificador pseudonimizado estável, base legal/finalidade, consentimento aplicável e retenção definida | Pendente; minimização deve anteceder a análise |
| Impacto de sustentabilidade | Perda real e destino, unidade/peso, conversão documentada e fator de impacto com fonte | Pendente até haver dados físicos e método rastreável |

## Critérios mínimos de publicação

Cada KPI promovido ao dashboard precisa apresentar:

- nome compreensível e pergunta de decisão;
- definição, população, grão, unidade, janela e fórmula;
- numerador e denominador quando aplicável;
- origem e data/corte do dado;
- regras de inclusão e exclusão;
- proprietário funcional e técnico;
- teste de qualidade/reconciliação;
- interpretação para zero, `NULL`, amostra pequena e dado atrasado;
- classificação: disponível, condicional ou pendente.

## Linha de base observada

O material de BI de 30/10/2026 registra 101 vendas concluídas, R$ 1.515,00 de
receita, ticket médio de R$ 15,00, pagamentos conciliados em PIX, 210 unidades
disponíveis segundo o snapshot carregado e R$ 2.100,00 estimados a custo médio.
Essa base foi usada para validar o cálculo, mas continha um único dia, uma loja
vendedora e um produto vendido. Não sustenta tendência, sazonalidade, comparação
representativa entre lojas ou inferência de preferência de pagamento. Confirme o
lote atual antes de reutilizar esses números.
