# Pesquisa de experiência do usuário

## Objetivo

A documentação de UX do primeiro ano investigou como apresentar a proposta do Mottainai e como tornar tarefas administrativas compreensíveis. Os registros combinam ideação, personas, arquitetura da informação, testes moderados, análise heurística e priorização. Os resultados são evidências exploratórias do grupo, não uma pesquisa representativa de todo o público.

## Perfis considerados

A pesquisa inicial descreve quatro perfis: gestão/supervisão, operação de estoque, consumidor e operador de caixa. A jornada da landing page detalha sobretudo a pessoa que conhece a solução, avalia funcionalidades e planos e busca contato. O painel administrativo atende quem cadastra e consulta dados da operação.

Esses perfis vieram de etapas e artefatos diferentes; devem ser tratados como hipóteses de design, não como segmentos validados por amostra estatística.

## Método e evidências

- Landing page: teste moderado com oito tarefas guiadas; os registros de resultado detalham três participantes e observações sobre compreensão da proposta e navegação.
- Painel CRUD: teste moderado com sete tarefas guiadas; quatro participantes avaliaram navegação, cadastro, consulta, edição e exclusão.
- Avaliação heurística: revisão baseada nas dez heurísticas de Nielsen.
- Priorização: severidade de 0 a 4 combinada com recorrência observada; esforço classificado em baixo, médio ou alto.

Os tamanhos de amostra são pequenos. As notas e observações ajudam a localizar fricções, mas não permitem generalização estatística.

## Achados principais

### Landing page

1. A proposta de controle de estoque foi entendida rapidamente, mas o diferencial do produto precisava aparecer com mais clareza.
2. O seletor de planos anual tinha área de interação pequena e feedback insuficiente.
3. O carrossel de “Sobre nós” avançava depressa e não oferecia controle de pausa.
4. Cards pareciam clicáveis mesmo quando não tinham ação.
5. O termo “ERP” precisava de explicação em linguagem cotidiana.
6. Texto provisório reduzia a confiança na apresentação.

### Painel administrativo

1. O motivo para bloquear a edição de CPF não estava explicado.
2. A máscara de CPF apresentou falha durante os testes.
3. A exclusão gerava receio e o modal não destacava o registro afetado com clareza.
4. O estado após salvar precisava de confirmação visível.
5. Filtros de situação tinham baixa visibilidade.
6. Parte das pessoas tentou abrir detalhes clicando na linha, embora a interação estivesse nos ícones.

## Prioridades recomendadas nos registros

**Alta prioridade:** melhorar feedback após ações; tornar a exclusão explícita e recuperável quando possível; explicar campos bloqueados; ampliar a área e o estado visual do seletor anual; dar controle ao carrossel; substituir conteúdo provisório.

**Prioridade seguinte:** melhorar a descoberta de filtros, a affordance dos cards e o acesso aos detalhes; explicar termos técnicos com exemplos.

As prioridades são recomendações históricas geradas pela pesquisa. Antes de aplicá-las ao produto atual, confirme se o fluxo ainda existe e valide a solução com usuários atuais.

## Limitações

Os artefatos originais usam recortes pequenos e misturam perfis e tarefas diferentes. A ideação completa também foi mantida em apresentação externa. Este resumo preserva os achados registrados no repositório, sem atribuir aos testes conclusões que eles não mediram.
