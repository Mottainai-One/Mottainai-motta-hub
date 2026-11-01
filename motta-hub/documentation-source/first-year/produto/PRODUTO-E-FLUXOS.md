# Produto e fluxos de interface

## Contexto

O primeiro ano documentou dois produtos de interface relacionados ao Mottainai: uma landing page institucional e um painel administrativo de cadastros. As telas descritas refletem os protótipos e requisitos acadêmicos daquele período. O hub de catálogo desenvolvido posteriormente é um produto distinto; suas permissões e fluxos vigentes estão documentados na raiz do projeto.

## Landing page

A navegação institucional organiza a apresentação em:

- **Início:** proposta de valor, funcionalidades e indicadores de impacto;
- **Sobre nós:** propósito, equipe e contexto do produto;
- **Planos:** opções de assinatura e comparação mensal/anual;
- **Perguntas frequentes e contato:** respostas iniciais e encaminhamento de dúvidas.

A comunicação deve explicar o benefício antes de recorrer a jargões, apresentar conteúdo final no lugar de texto provisório e indicar claramente quais elementos são interativos.

## Painel administrativo

O painel conceitual oferece login, visão inicial e navegação lateral para empresas, lojas, funcionários, cargos, contas de usuário e planos de assinatura. As telas CRUD agrupam listagem, busca/filtro, consulta de detalhes e ações de criação, edição e exclusão.

### Requisitos transversais registrados

- Exibir confirmação após operações concluídas e mensagens úteis diante de erros.
- Validar campos e explicar restrições, inclusive identificadores não editáveis.
- Identificar com clareza o registro e o efeito de uma exclusão.
- Dar destaque aos filtros e manter consistência entre linha, ícones e ações.
- Projetar controles com área de interação adequada e feedback de estado.
- Adaptar a navegação e os componentes a diferentes larguras de tela.

## Princípios de interação

1. Usar rótulos familiares e explicar termos especializados.
2. Manter o usuário informado durante carregamento, salvamento e falha.
3. Prevenir ações destrutivas e oferecer confirmação contextual.
4. Tornar as restrições visíveis no ponto em que afetam a tarefa.
5. Não sugerir clique em elementos que não executam uma ação.
6. Revalidar decisões com usuários antes de transportá-las para o hub atual.

## Relação com a pesquisa

Os requisitos acima consolidam a arquitetura das telas e os achados resumidos em [Pesquisa de experiência do usuário](PESQUISA-UX.md). Os registros de testes sustentam fricções como feedback insuficiente, exclusão pouco clara, filtro pouco visível e controle inadequado do carrossel. Eles não demonstram que cada sugestão foi implementada nem que continua válida no produto atual.
