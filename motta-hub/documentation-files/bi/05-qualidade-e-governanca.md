# Qualidade, governança e segurança do BI

## Princípios

- o banco operacional é a fonte do estado transacional;
- o banco analítico mantém uma publicação para consulta histórica e agregação;
- o dashboard só lê a Gold governada;
- todo valor publicado deve ter linhagem e definição verificável;
- ausência de dado não deve ser mascarada como valor zero;
- somente os dados necessários à pergunta de BI atravessam as camadas;
- segredos e credenciais nunca são conteúdo de notebooks, arquivos de dashboard,
  documentação ou logs.

## Dimensões de qualidade

| Dimensão | Verificação esperada | Evidência operacional |
|---|---|---|
| Completude | Relações esperadas presentes; campos obrigatórios preenchidos | Contagem por relação e regras Silver |
| Unicidade | Chaves únicas no grão de cada dimensão/fato | Duplicatas registradas como achados |
| Integridade referencial | Fato encontra empresa, loja, produto e venda aplicáveis | Anti-joins de qualidade Silver |
| Validade | Tipo, intervalo e domínio aceitos | Casts e regras por status/medida |
| Consistência | Venda, itens e pagamentos se reconciliam na população elegível | Reconciliação Silver/Gold |
| Atualidade | Batch, corte e publicação são explícitos | `dashboard_freshness`, tabela de controle |
| Exatidão observável | Contagens e somas comparam origem/publicação | Logs e contagens do contrato RPA |

Zero erros detectados em regras internas não prova que todos os dados de origem
são corretos. A reconciliação e a cobertura da população também precisam ser
avaliadas.

## Gating de publicação

1. **Preflight:** validar identidade/conexão, database esperado, leitura de
   diagnóstico no operacional e batch analítico elegível.
2. **Bronze:** conferir que todas as relações contratadas existem e capturar
   contagens do mesmo batch.
3. **Silver:** calcular resultados de regra, chaves, duplicidade, relações e
   reconciliação financeira.
4. **Gold:** promover apenas o batch aceito; preservar a publicação anterior
   caso haja bloqueio.
5. **Dashboard:** atualizar apenas depois de Gold; confirmar que o objeto
   publicado aponta para a versão nova e não embute credenciais.

Falhas impeditivas devem parar a publicação, criar evidência acionável e manter
o marcador anterior. Avisos não impeditivos precisam ter dono, prazo e impacto
declarado no dashboard/runbook.

## Privacidade e minimização

A carga e os notebooks BI devem selecionar apenas campos necessários. As
revisões locais da carga afirmam exclusão de documentos, nomes, e-mails,
telefones, credenciais e hashes de senha do consumo BI. A Bronze do dashboard
minimiza IDs de funcionários/clientes não necessários. Confirmar a consulta de
origem sempre que novos campos forem incluídos; mascarar na Gold não justifica
copiar dado pessoal desnecessário para Bronze.

Para qualquer análise de cliente, funcionário ou comportamento individual,
documentar finalidade, base legal/consentimento aplicável, identificador
pseudonimizado, acesso, retenção e risco de reidentificação antes de implementar.
Não usar chaves criptográficas ou segredos da aplicação como mecanismo de
anonimização analítica.

## Acesso

- conexões PostgreSQL: conceder acesso mínimo às identidades de job necessárias;
- escrita Delta: reservar às identidades de execução do bundle;
- consumo Gold: conceder `SELECT` aos analistas/leitores autorizados;
- dashboard e SQL Warehouse: revisar permissões juntos, pois a leitura depende
  dos dois recursos;
- publicação: manter `embed_credentials=false` e não publicar token/conexão em
  URL ou documento.

Compartilhamento do dashboard não deve, por si só, ampliar o acesso aos bancos
físicos. Revisar permissões por grupo e revogar acesso quando a equipe/atividade
terminar.

## Evolução do contrato e mudança de KPI

Mudanças de esquema devem ser compatíveis com o RPA, Bronze, Silver, Gold e
datasets do painel. Uma mudança em grão ou significado exige versão explícita ou
migração com plano de replay. Uma alteração de fórmula exige atualizar catálogo,
dicionário no dashboard, consultas Gold, interpretação, evidência e runbook na
mesma entrega.

PR de BI deve conter pelo menos:

- objetivo e decisão que a mudança suporta;
- tabela de origem e linhagem;
- definição e estado dos KPIs afetados;
- resultado de validação de dados e consultas;
- impacto em custo/compute e frequência;
- tratamento de falha, vazio e reexecução;
- evidência visual da versão publicada;
- mudanças no catálogo e no runbook.

## Custos e limites

O BI deve manter uma execução diária após o lote, limitar concorrência e preferir
SQL/Datasets Gold reutilizáveis a recomputação duplicada por widget. Validar
volume e duração antes de aumentar a frequência. A frequência de carga e o
horário de painel devem refletir os requisitos operacionais, não uma expectativa
implícita de tempo real.
