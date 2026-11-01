# Mobile Cliente — plano de implementação por etapas e PRs

> **Histórico, substituído na atribuição de responsabilidades:** a execução vigente está no [plano somente Mobile Cliente](PLANO-MOBILE-CLIENTE.md). Isabella definiu posteriormente que esta frente altera apenas o Android; API, PDV, IA e banco são de outra equipe, orientada por [DEMANDAS-API-CLIENTE.md](DEMANDAS-API-CLIENTE.md). As tabelas abaixo registram o planejamento inicial, não o estado mais recente nem autorização para implementar backend ou abrir PR.

> Versão inicial para alinhamento, **21/10/2026**, com conferências de código e PRs realizadas em 20/10. Este plano não autoriza push, abertura de PR, merge, configuração de serviços ou migration de banco. Cada envio depende de confirmação de Isabella. Os códigos `PR-01` etc. são identificadores do plano, não números de PR já aberta.

## 1. Objetivo e regras que não mudam

Entregar o Cliente como uma vitrine autenticada de ofertas próximas, com direcionamento à loja, avisos de proximidade e impacto sustentável baseado em pontos de compras comprovadas.

- Conta/login obrigatório antes de acessar os serviços; demonstração é somente ferramenta debug.
- Firebase somente para autenticação. Não introduzir Firestore, Firebase Storage ou FCM por conveniência.
- Sem catálogo, perfil, pontos ou chat offline no Cliente. Offline de negócio é do Operacional.
- Mapear mercados pela localização atual e filtrar suas promoções disponíveis.
- Ordenar por proximidade e, depois, maior **desconto percentual**. Não trocar a prioridade por valor economizado em reais.
- Segundo a regra comercial informada, maiores descontos já refletem vencimento mais próximo; não adicionar uma prioridade de validade que sobreponha a ordenação confirmada.
- Detalhe abre o Google Maps oficial, app ou site, com a unidade que anunciou a promoção.
- Compra exclusivamente no mercado: sem checkout, pagamento, cashback, cupons ou resgate no MVP.
- Raios 5/10/15/20 km, padrão 5 km, na confirmação do endereço. Localização obrigatória; avisos no mesmo raio, somente de parceiros, online e com suporte a segundo plano.
- Cada loja pode enviar até três avisos/dia, de produtos diferentes; quota centralizada de loja/dia e deduplicação por destinatário, sem multiplicar campanhas por aparelho.
- Um ponto por real gasto em compra confirmada no PDV e vinculada pelo CPF; cancelamento/devolução estorna crédito. Pontos priorizam comunicações e representam participação no programa. Não adicionar o bônus promocional anteriormente cogitado.
- Avatar somente Cloudinary; produtos via API externa a identificar; oferta reutiliza imagem do produto.
- Dados de negócio passam pela API e persistência autorizada. Não enviar credenciais de banco/armazenamento ao Android.
- Não criar métricas, fotos, localização, compras ou respostas de IA fictícias no modo real.

Referência de produto: [documentação principal](../MOBILE-CLIENTE.md).

Pesquisa e proposta de níveis/imagens: [fidelidade e imagens](FIDELIDADE-E-IMAGENS.md). Faixas Semente/Broto/Planta/Árvore/Floresta são proposta inicial Mottainai, não métricas ambientais; Open Food Facts recomendado para piloto, condicionado a cobertura e termos.

## 2. Base real antes de começar

### 2.1 O que deve ser reaproveitado

| Item | Estado conferido | Consequência para o plano |
| --- | --- | --- |
| Cliente `fix/firebase-auth-only` | Código alterado localmente, ainda não enviado | Preparar uma entrega pequena; não reescrever login/cadastro |
| Testes locais dessa alteração | 17 testes JVM aprovados; núcleo de autenticação compilado diretamente | Não equivale a APK/lint/telas homologados |
| Catálogo e lojas | Repositórios, paginação, busca, filtro por loja, detalhe e mapa existentes | Estender o contrato geográfico, não criar outro catálogo |
| Proximidade de lojas | Busca manual em 5 km existente | Ainda não é feed geográfico compartilhado nem geofencing |
| Rota | `MapNavigation` usa `geo:` genérico; detalhe já chama esse auxiliar | Ajustar o auxiliar e seus consumidores, não duplicar botão/fluxo |
| Pontos | Consulta de saldo e seis janelas mensais existente | Não prova concessão por compra nem cálculo de impacto |
| Perfil | API retorna representação protegida, sem nome legível | Não ler hash como nome nem voltar a gravar nome no Firebase |
| API #60 | PR aberta para preservar telefone omitido | Revisar/reutilizar a PR existente; não abrir uma duplicada |
| Catálogo Firebase | Referência API `83c08fa` já inclui as rotas na cadeia Firebase | Validar ambiente; não repetir a correção como funcionalidade nova |
| Hub | Documentação enviada na branch `fix/mobile-cliente-documentacao`, commit `94428eb`, sem PR | Este plano é um acréscimo local; não está publicado automaticamente |

O repositório que contém os contratos atuais é [API SQL Operacional](https://github.com/Mottainai-One/Mottainai-Api-SQL-Operacional), anteriormente `Mottainai-Spring-Api-SQL`. Também existe [API SQL Cliente](https://github.com/Mottainai-One/Mottainai-Api-SQL-Cliente): sua `main` examinada em 21/10 contém somente `LICENSE`, com outras branches ainda não auditadas. Antes de qualquer entrega backend, alinhar o repositório responsável e o reaproveitamento/migração compatível dos contratos; não duplicar nem assumir que o serviço separado está pronto. PR-02/#60 permanece no repositório original.

### 2.2 PRs existentes: organizar antes de empilhar novas entregas

Consulta somente leitura em 20/10 confirmou abertas as PRs do Cliente abaixo:

```text
#10 draft (frontend, base main)
  -> #11 autenticação
  -> #13 tema/espaçamento
  -> #12 catálogo/navegação
  -> #16 localização
  -> #17 histórico de pontos
  -> #14 Home/perfil
  -> #15 isolamento da demonstração
  -> #18 CI
  -> PR-01 deste plano, hoje somente local
```

Também estão abertas as PRs antigas #3, #4, #6, #7, #8 e #9. Revisar sobreposição antes de qualquer merge/fechamento; não incorporar implementações antigas cegamente e não excluir trabalho de terceiros.

**Portão de entrada:** escolher com a equipe como homologar a base, inclusive o frontend draft. Não mergear #10 como pronta só porque outras PRs dependem dela. Não fazer force push, rebase compartilhado, fechamento ou merge sem autorização. Depois da consolidação, preferir novas branches a partir da `main` aprovada; usar stack somente quando a dependência for explícita.

## 3. Decisões que destravam as etapas

Não é necessário responder tudo para começar. Cada decisão bloqueia somente as entregas indicadas.

| Código | Decisão pendente | Bloqueia |
| --- | --- | --- |
| D01 | Raios 5/10/15/20 km e localização obrigatória confirmados; falta comportamento de região sem ofertas | Aceite final PR-03/04 |
| D02 | Distância exata versus faixas de proximidade, desempate de distância e desconto para promoções com vários itens | Contrato de ordenação PR-03 |
| D03 | Atualizar localização ao abrir, ao mover ou por ação explícita | PR-04 |
| D04 | Mesmo raio e três avisos de produtos distintos por loja/dia confirmados; faltam fuso/horário e destino do toque | PR-06/07/20 |
| D05 | Online e segundo plano confirmados; falta especificar retomada/reinício e validar permissões/restrições | PR-06/07 |
| D06 | PDV com vínculo pelo CPF confirmado; falta contrato autenticado de eventos e identificação única da venda | PR-08/09/10/11 |
| D07 | 1 ponto por real sobre total gasto e estorno confirmados; faltam centavos e devolução parcial | PR-09/10/11 |
| D08 | Faixas propostas em FIDELIDADE-E-IMAGENS; falta validar período/expiração, sem equivalência ambiental | PR-10/11 |
| D09 | Leitura autorizada do perfil e fonte recuperável dos dados protegidos | PR-12/13 |
| D10 | Cloudinary avatar confirmado; Open Food Facts recomendado para piloto de produtos, pendente cobertura/termos | PR-14/15/16 |
| D11 | Reutilizar agente consumidor existente; falta autorização Firebase consumidor e fontes disponíveis | PR-17/18 |
| D12 | Manter campos do banco/contrato; verificar compatibilidade dos formulários, sem nova coleta por suposição | PR-19 |
| D13 | Mais pontos recebe primeiro, confirmado; faltam limite do primeiro grupo, empate e janela de antecedência | PR-20 |

Os 5 km são agora padrão aprovado, não apenas fixture da busca manual. Demais opções e fórmulas não devem ser inferidas. Registrar as preferências de raio no contrato oficial, sem transformá-las em histórico de rastreamento.

## 4. Mapa de etapas e unidades de revisão

O plano separa até **20 unidades de revisão**, incluindo #60 e o trabalho local existente. Não significa abrir todas agora. O novo item PR-20 atende prioridade por fidelidade e quota centralizada; sua numeração não define ordem cronológica.

| Etapa | ID | Repositório | Entrega / branch proposta | Dependências |
| --- | --- | --- | --- | --- |
| A — Base | PR-01 | Cliente | Firebase somente Auth — `fix/firebase-auth-only` | Consolidar/revisar base existente |
| A — Base | PR-02 | API | Telefone omitido — **reutilizar #60** | Review e publicação aprovados |
| B — Vitrine | PR-03 | API | Ofertas geográficas — `feat/customer-nearby-promotions` | D01/D02 |
| B — Vitrine | PR-04 | Cliente | Home/Catálogo/mapa próximos — `feat/nearby-offers` | PR-03 + D01/D03 |
| B — Vitrine | PR-05 | Cliente | Destino Google Maps — `fix/google-maps-destination` | PR-01/base; independente da fórmula de pontos |
| C — Proximidade | PR-06 | Cliente | Preferências, canal e permissões — `feat/proximity-notifications` | D04/D05 |
| C — Proximidade | PR-07 | Cliente | Geofences e avisos locais — `feat/store-geofencing` | PR-04/06 + contrato de ofertas elegíveis |
| D — Impacto | PR-08 | API / integração aprovada | Compra comprovada — `feat/customer-purchase-proof` | D06 e contrato aprovado |
| D — Impacto | PR-09 | API | Pontos de compra — `feat/purchase-impact-points` | PR-08 + D07 |
| D — Impacto | PR-10 | API | Consulta de impacto — `feat/customer-impact-summary` | PR-09 + D08 |
| D — Impacto | PR-11 | Cliente | Pontos e impacto real — `feat/customer-impact` | PR-09/10 publicados |
| E — Perfil | PR-12 | API | Perfil próprio legível autorizado — `feat/customer-profile-display` | D09 + PR-02 quando aplicável |
| E — Perfil | PR-13 | Cliente | Perfil oficial — `feat/customer-profile-data` | PR-12 publicado |
| F — Imagens | PR-14 | API | Upload e referências de mídia — `feat/customer-media` | D10; storage autorizado |
| F — Imagens | PR-15 | Cliente | Avatar persistido — `feat/customer-avatar` | PR-12/14 publicados |
| F — Imagens | PR-16 | Cliente | Fotos reais das ofertas — `feat/offer-images` | Referência de imagem publicada em PR-14 |
| G — Assistente | PR-17 | IA | Identidade/escopo consumidor — `feat/customer-assistant-access` | D11 + vínculo de cliente oficial |
| G — Assistente | PR-18 | Cliente | Chat real — `feat/customer-assistant` | PR-17 publicado |
| H — Aceite | PR-19 | Cliente | Ajustes/testes finais — `fix/customer-release-readiness` | Entregas aceitas; somente se houver alteração revisável |
| C/D — Distribuição | PR-20 | API responsável a confirmar | Prioridade e quota — `feat/loyalty-offer-priority` | PR-09 + D04/D13; integrar PR-07 |

Cada PR deve ter normalmente **1–3 commits**, código acompanhado dos testes pertinentes e descrição do contrato usado. Se uma entrega ultrapassar um escopo revisável, dividir por contrato ou fluxo; não atingir a meta de commits agrupando mudanças sem relação.

## 5. Etapa A — consolidar conta, sessão e segurança de gravação

### PR-01 — finalizar o trabalho local de Firebase somente Auth

- **Reaproveitar:** `AuthRepository`, `ProfileSyncStatus`, `AuthViewModel`, telas de entrada/cadastro/perfil e testes alterados localmente.
- **Entregar:** não ler/gravar display name; nome enviado somente à API; perfil com ID positivo, HTTP confirmado e situação ativa; recuperação de sincronização sem duplicar conta; sem visitante em produção.
- **Aceite:** senha e Google, conta sem perfil, conta inativa, resposta incompleta, troca de conta, rotação, falha de rede e demonstração restrita a debug.
- **Testes:** manter os 17 JVM, executar build/lint/roteiro Android no ambiente autorizado. A compilação direta anterior do núcleo não substitui APK nem valida todas as Activities.
- **Fora da PR:** não contornar o perfil protegido com cache de nome, Firebase ou nova tabela improvisada.

### PR-02 — reutilizar a API #60

- [PR existente #60](https://github.com/Mottainai-One/Mottainai-Api-SQL-Operacional/pull/60): preservar telefone quando omitido/null, manter diferenciação de limpeza explícita e substituição.
- Conferir compatibilidade com a `main` atual, testes e versão publicada; não assumir que o checkout local ou a PR aberta já esteja implantado.
- **Aceite integrado:** editar nome/consentimento sem apagar telefone. Não marcar essa segurança de gravação aprovada sem a correção no ambiente.

## 6. Etapa B — completar a vitrine por proximidade

### PR-03 — backend do feed geográfico

- Estender o contrato de promoções existente; publicar nomes/tipos dos parâmetros antes do Android. Reutilizar a infraestrutura de coordenadas e busca geográfica de lojas quando adequada.
- Filtrar mercados elegíveis na região **antes de paginar**. Não buscar uma página global e retirar itens no Android; isso produz ordenação e paginação incorretas.
- Ordenar por proximidade, desconto percentual e desempate determinístico aprovado. Definir comparação de promoções com vários itens e tratamento de preço original ausente/zero; não dividir por zero nem fabricar percentual.
- Manter aprovação, atividade, vigência, loja ativa e disponibilidade. Detalhe e lista precisam aplicar regras coerentes.
- **Testes:** lojas dentro/fora do raio, coordenadas ausentes, limites válidos/inválidos, mesma distância, diferentes percentuais, paginação estável e promoções inelegíveis.
- **Aceite:** exemplos de contrato e dados de teste mostram que uma oferta distante com desconto alto não sobe acima da prioridade geográfica aprovada.

### PR-04 — contexto geográfico compartilhado no Cliente

**Continuação local de 21/10:** Home e Lojas agora compartilham ViewModel para a consulta geográfica de lojas e raio, sem posição persistida. Home orienta definir posição em Lojas e não consulta uma lista global substituta. Main/detalhe/assistente usam bloqueio central de sessão/permissão/localização do aparelho, com tela de recuperação e saída da conta. Sete testes da política de acesso adicionados; conjunto JVM totaliza 36 aprovados. Nenhum build APK/lint/UI executado. Feed de promoções próximo, preferência oficial no cadastro, notificações e backend continuam pendentes.

**Recorte local implementado em 21/10:** tela de Lojas seleciona 5/10/15/20 km pelo contrato existente, mantém raio em ViewModel/Bundle e reinicia páginas/invalida respostas anteriores ao mudar região/raio. Sem posição, a tela não consulta lista geral; revogação/GPS desligado ao retornar limpa resultados. Não inclui ainda preferência oficial no cadastro, feed de promoções geográfico, compartilhamento entre telas ou bloqueio global. Nenhum push/PR deste recorte.

Validação do recorte anterior: 17 testes JVM (5 opções de raio, 7 destinos Maps, 5 paginação), 58 XMLs e Manifest analisados; ViewModel/repositório/DTOs atuais compilados diretamente com dependências em cache. A continuação acima atualiza o total para 36 testes e 59 XMLs; Activities/Fragments e APK ainda precisam de compilação/homologação Android. Home passou a usar `loadNearbyStores`; promoções ainda usam o contrato anterior.

Conferência adicional somente leitura: branch `chore/initial-project-setup` da API Cliente contém aplicação inicial/pom/configuração/teste de contexto; `ci/project-quality-checks` contém CI/documentação. As duas árvores retornaram completas, sem controller de catálogo nessas versões. Confirmar com a equipe o repositório responsável antes de criar implementação backend; não migrar contratos entre APIs implicitamente.

- Reaproveitar `CatalogRepository`, `CatalogViewModel` e a tela de lojas. Fazer Home, Catálogo e mapa usarem o mesmo contexto de localização aprovado, sem copiar toda a lógica para cada tela.
- Na confirmação do endereço, oferecer os raios aprovados com padrão 5 km e persistência pelo contrato oficial. Solicitar localização no contexto adequado. Recusa bloqueia serviços conforme produto, mas preserva login/recuperação e orientação para conceder permissão. Tratar posição aproximada, GPS desligado e timeout sem inventar localização.
- Atualizar o feed pelo gatilho D03, manter filtros/busca/paginação, descartar respostas de uma região anterior e permitir recuperação de erros por seção.
- **Aceite:** mudar posição/região muda as ofertas e os pins de forma coerente; navegação e rotação não misturam páginas de regiões distintas; não há banco offline de ofertas.

### PR-05 — Google Maps oficial e unidade correta

**Implementado localmente em 21/10:** `MapNavigation` prefere pacote oficial e usa URL web como alternativa; `GoogleMapsUrl` seleciona coordenadas/endereço completo da unidade, sem iniciar navegação automática. Sete testes JVM aprovados. Não enviado, sem PR aberta; homologação Android pendente. Alterações locais anteriores foram preservadas, sem criar branch/commit automaticamente.

- Alterar o auxiliar compartilhado `MapNavigation` e conferir detalhe/lista/pins. O botão no detalhe já existe no código; não criar outro fluxo concorrente.
- Usar o destino da unidade da promoção, coordenadas válidas ou endereço completo; Maps URL/intents conforme o contrato escolhido. Não usar nome genérico da rede como destino.
- Abrir Google Maps oficial e ter alternativa web; tratar ausência de destino e de aplicativo capaz de abrir a URL. Não iniciar compra nem enviar token Firebase ao Maps.
- **Testes:** unidade A/B da mesma rede, caracteres especiais, coordenadas inválidas/ausentes, app Maps instalado/desativado/ausente e retorno ao app.
- **Aceite:** o destino marcado corresponde exatamente à promoção selecionada. Início de navegação/forma de transporte depende de A09 do documento de produto, não de uma escolha silenciosa.

## 7. Etapa C — notificações de proximidade, sem Firebase adicional

### PR-06 — permissões e preferências

- Criar canal de notificação local e fluxo contextual de autorização. Tratar `POST_NOTIFICATIONS` nas versões aplicáveis; não pedir tudo no cadastro.
- Separar permissão de localização da preferência de receber avisos. Incluir ativar/desativar e explicação do que será monitorado, após D04/D05.
- Fazer o toque validar sessão e conteúdo antes de abrir loja/oferta. Depois de logout, não expor dados ou aplicar ações em nome da conta anterior.
- **Aceite:** recusar notificação não bloqueia mapa/feed; desligar avisos interrompe o comportamento; não há FCM, registro de push ou transporte externo obrigatório.

### PR-07 — regiões e confirmação da oferta

- Proposta técnica: usar geofencing do Google Play services para receber transições, sem loop de GPS contínuo. Confirmar suporte e dependência necessária antes de adicioná-la.
- Registrar somente regiões de lojas elegíveis; respeitar o limite da plataforma e renovar/remover registros conforme região, conta, permissões e preferências. Não registrar todo o país.
- Em uma transição autorizada, confirmar ofertas vigentes e autorização de comunicação pela API (PR-20). Usar o mesmo raio do feed; sem rede, não emitir aviso. Não afirmar disponibilidade a partir de snapshot antigo.
- Deduplicar pelo critério aprovado e tratar permanência/reentrada. Logout/troca de conta deve remover ou invalidar monitoramento e trabalho pendente.
- **Estado técnico mínimo:** identificadores de regiões, configuração e controle de repetição podem precisar de persistência local restrita à conta; isso não é catálogo offline nem autorização para Room/cache de negócio. Especificar retenção e limpeza.
- **Background confirmado:** solicitar permissões específicas de forma contextual/separada e testar segundo plano em aparelho. Recusa de background impede monitoramento fora da tela, não invalida localização em primeiro plano já concedida. Definir retomada/reinício sem prometer funcionamento após force-stop ou entrega instantânea.
- **Testes:** ausência de rede, sessão expirada, loja sem oferta, oferta expirada, notificações negadas, duas lojas próximas, duplicidade, mudança de conta, economia de bateria e aparelho real.
- **Aceite:** proximidade gera aviso da unidade parceira certa, respeitando prioridade e quota, sem repetição indevida. Geofencing local não substitui o controle central de distribuição; não introduzir FCM ou outro transporte sem aprovação. Suporte ao background depende de D05.

## 8. Etapa D — compra comprovada, pontos e impacto

Essa etapa **não começa pela animação de uma tela**. Primeiro precisamos saber como uma compra fora do app se torna um evento confiável.

### PR-08 — contrato e validação da compra

- A origem será o PDV Mottainai. D06 define como identificar o cliente e integrar venda/itens/estorno, não se deve criar comprovação por OCR/QR no Cliente sem necessidade. O caminho de venda examinado em `main` do POS usa mocks e o modelo tem cliente opcional; isso não prova integração pronta. Conferir branches/serviço responsável antes de alterar o PDV.
- Usar o registro de venda/itens existente se ele atender ao contrato; somente propor estrutura nova após conferir o schema oficial.
- Publicar vínculo com cliente/unidade/itens/quantidades, origem comprovável, identificação única e estados de confirmação/cancelamento.
- Impedir que o consumidor envie apenas produto/quantidade e declare unilateralmente uma compra válida. Clicar em oferta, abrir Maps ou passar perto da loja não concede pontos.
- **Aceite:** uma compra pode ser vinculada uma única vez ao dono correto; origem não autorizada e tentativa de vincular compra de outro cliente são recusadas.
- **Escopo externo:** se for necessário alterar o app Operacional/caixa, preparar uma entrega própria no repositório responsável e pedir aprovação. Isso não está autorizado implicitamente por uma PR Android Cliente.

### PR-09 — concessão de pontos no backend

- Aplicar 1 ponto por real sobre o total gasto confirmado, com versão/regra e testes. Definir centavos antes de calcular. Não aplicar bônus promocional, percentual de desconto ou valor economizado como multiplicador.
- Reutilizar conta/histórico de pontos existentes, preservando titularidade. Garantir transação, idempotência e proteção contra crédito duplicado/concorrrente.
- Registrar relação com a compra e estornar os pontos ganhos quando houver cancelamento/devolução, de forma auditável e idempotente, sem apagar o original. Definir devolução parcial, concorrência e tratamento de saldo antes da implementação.
- Não integrar endpoints legados de recompensas ao Cliente. Não remover funções de outros consumidores da API sem análise e autorização específicas.
- **Aceite:** replay não soma novamente; R$ 100 elegíveis geram 100 pontos; cancelamento estorna o crédito; centavos/devolução parcial têm testes segundo regra aprovada; Android não concede pontos.

### PR-10 — cálculo e consulta de impacto

- Definir se o impacto usa pontuação acumulada válida, lançamentos por período ou outro agregado. Não assumir que saldo atual e impacto histórico são a mesma coisa.
- Publicar consulta autenticada de resumo/histórico, unidades, período, data de atualização e versão do cálculo. Nomes de novas rotas só serão definidos no contrato, não inventados neste plano.
- Se houver kg/CO₂, exigir dados e fatores aprovados. A finalidade sustentável dos pontos não transforma uma pontuação, sozinha, em medição física comprovada.
- **Aceite:** períodos, ausência de compras, estornos e versões da fórmula têm resultado reproduzível; consultar outro cliente é proibido.

### PR-11 — apresentar pontos e impacto reais

- Reaproveitar saldo/histórico mensal atuais; integrar o resumo real e a navegação com Impacto/Home.
- Substituir placeholders de impacto apenas quando houver contrato publicado. Apresentar unidade, período, origem e eventual caráter estimado de métricas conforme a regra oficial.
- Adequar a linguagem a “pontos de fidelidade” e “status sustentável”; explicar prioridade de comunicação sem insinuar resgate, cashback ou reserva.
- **Aceite:** compra de teste confirmada altera pontos/impacto conforme o servidor; estorno atualiza de forma coerente; vazio e erro não viram métricas demonstrativas.

## 9. Etapa E — completar perfil sem depender do Firebase como cadastro

### PR-12 — representação autorizada do perfil próprio

- Resolver D09 com a equipe API/banco. A representação protegida atual não devolve nome legível; hashes não podem ser transformados de volta em texto.
- Se houver fonte recuperável autorizada, usá-la com mínimo de exposição. Se não houver, desenhar o armazenamento protegido e a origem/backfill legítima antes de criar leitura. Não recriar dados perdidos nem restaurar colunas pessoais por conveniência.
- Publicar campos realmente necessários à tela, permissões de leitura/edição e atualização parcial que preserve campos não enviados.
- **Aceite:** cliente só lê/edita seus dados; logs/JSON não expõem tokens de proteção como contato; cadastro e GET mantêm contrato consistente; PR-02 aplicada quando necessária.

### PR-13 — perfil oficial no Android

- Adaptar DTO e formulário ao contrato publicado. Não retirar `transient` dos campos de proteção sem saber o significado e a autorização da nova resposta.
- Exibir nome oficial, contato permitido e preferências; preservar entrada em falha e evitar pedidos redundantes de nome quando o backend puder omiti-lo/retorná-lo com segurança.
- **Aceite:** sair/entrar/recarregar recupera o perfil autorizado; editar sem telefone não o apaga; não há gravação em Firebase ou cache de nome para substituir a fonte oficial.

## 10. Etapa F — avatar e imagens de ofertas

### PR-14 — backend de mídia e referências

- Avatar usa somente Cloudinary, com upload autorizado e credenciais privadas no servidor. Produtos vêm de API externa ainda não identificada; são contratos distintos. Não escolher Firebase Storage nem colocar segredo de upload no Android.
- Reutilizar campos de imagem existentes quando houver. Publicar referências autorizadas de avatar e fotos de produto/oferta; quem publica imagem de produto pertence ao fluxo operacional autorizado, não ao cliente consumidor.
- Definir envio, confirmação da referência, tipo/tamanho, exclusão/substituição e tratamento de upload interrompido. Não persistir Base64 em tabelas relacionais por atalho.
- **Aceite:** cliente não altera avatar de outro usuário nem foto de produto; URL/objeto não confirmado não vira imagem persistida; arquivos inválidos e uploads incompletos são tratados.

### PR-15 — avatar no Cliente

- Seleção de imagem por recurso nativo Android, apresentação de progresso/erro, envio e confirmação pela API.
- Não tratar URI local como URL permanente; cancelar não sobrescreve o avatar anterior.
- **Aceite:** imagem persiste após novo login; falha de envio mantém a anterior; referência de outra conta não aparece; não adicionar câmera se seleção de arquivo atender ao requisito aprovado.

### PR-16 — imagens reais das ofertas

- Consumir a imagem do produto obtida da API externa aprovada e exposta pelo contrato do catálogo; oferta reutiliza essa foto. Definir identificação do produto, licença/atribuição e limites do provedor; placeholder em ausência/falha. Segredos do provedor ficam no servidor quando necessários.
- Reutilizar componente/dependência existente; avaliar dependência de imagens somente quando necessária. Não baixar/improvisar fotos de internet para preencher o catálogo.
- **Aceite:** card e detalhe usam a imagem do item/unidade corretos, sem bloquear a lista nem criar funcionalidade offline de ofertas.

Se avatar e fotos exigirem políticas/contratos muito diferentes, separar PR-14 por subcontrato. Não criar uma plataforma genérica de mídia para necessidades hipotéticas.

## 11. Etapa G — assistente consumidor

### PR-17 — autorização e contrato na IA

- Reutilizar o agente consumidor RAG existente em `app/agents/cliente.py` (IA `main` `021fdc0`, conferida em 21/10), com fontes autorizadas; não reconstruir o assistente. `/chat` aceita `message` e `session_id`, mas o resolvedor Firebase observado atende funcionário. Suporte ao papel CLIENTE em outro tipo de JWT não prova acesso Firebase consumidor pronto.
- Resolver identidade de cliente pelo vínculo oficial e manter sessões/histórico isolados por dono. Não atribuir empresa/cargo de funcionário a um cliente só para a chamada funcionar.
- Definir fontes permitidas: dúvidas e ofertas públicas autorizadas versus dados pessoais próprios, conforme produto. Nunca permitir acesso consumidor a dados operacionais internos.
- **Aceite:** clientes distintos não leem sessões um do outro; sessão inválida não cria escalada; cliente não assume papel de funcionário; chave de modelo fica no servidor.

### PR-18 — conversa real no Android

- Integrar envio, espera, erro, tentativa novamente e histórico online conforme o contrato publicado.
- Não repetir silenciosamente mensagens que possam gerar respostas duplicadas; definir a recuperação de resultado desconhecido conforme o serviço.
- **Aceite:** envio e reabertura do histórico online funcionam com conta real; troca de conta limpa o estado adequado; sem rede não há resposta local fictícia nem histórico offline de produção.

## 12. Etapa H — homologação e preparação da versão

### PR-20 — prioridade de comunicação e limite diário

- Publicar política do servidor para melhores ofertas/lotes menores e clientes elegíveis por fidelidade. Definir limiar, empate e janela de antecedência antes de codificar. Prioridade de envio não muda automaticamente a ordenação distância/desconto nem concede exclusividade, reserva ou garantia de estoque.
- Unificar quota de três avisos de produtos distintos por loja/dia. A seleção de campanhas é da loja, não três novos produtos para cada cliente. Cada campanha pode alcançar seus destinatários elegíveis sem contar cada destinatário como nova campanha. Garantir idempotência, concorrência, fuso e deduplicação por conta entre aparelhos.
- Não marcar entrega efetiva apenas por responder à consulta: definir reserva/expiração/confirmação da emissão e retentativas para não duplicar nem esgotar a quota silenciosamente. Sem internet, Android não emite aviso.
- Integrar compra/estorno oficial à pontuação elegível e revogar conteúdo que perdeu vigência. Registrar só o necessário à auditoria, sem histórico contínuo de localização.
- Testar limites, repetição do produto, múltiplas lojas/aparelhos, virada do dia, pontuações empatadas, oferta cancelada, estorno e usuário não autorizado. Só concluir PR-07 após esse aceite integrado.

### PR-19 — fechar ajustes reais de aceite

- Validar XML/Manifest, navegação/IDs, acessibilidade, fonte ampliada, teclado, rotação, campos obrigatórios, permissões e dispositivos suportados.
- Testar a cadeia completa: login → região → ofertas → detalhe → Google Maps; região → aviso → conteúdo revalidado; compra comprovada → pontos → impacto; perfil/avatar; assistente autorizado.
- Revisar HTTPS, assinatura, restrições Maps, configuração Firebase, isolamento de conta, logs e ausência de dados demonstrativos em produção.
- Executar testes/lint/build no CI e Android Studio conforme a responsabilidade combinada; anexar evidência honesta. Não marcar checklist por compilação direta de um subconjunto de fontes.
- Abrir uma PR somente se houver mudanças de código/teste/documentação a revisar. Um aceite manual sem alterações não exige PR vazia. Mudanças de configuração privada não vão para Git.
- **Conclusão:** todas as funções do escopo escolhido estão integradas e homologadas; funcionalidades ainda condicionadas não são declaradas prontas. Não usar prazo fixo como substituto dos contratos/dados/permissões que faltam.

## 13. Mudanças de banco: apenas se demonstradas necessárias

Possíveis entregas condicionais no repositório oficial do banco:

- **B-01 — perfil protegido recuperável:** somente se a fonte atual não atender à leitura autorizada aprovada.
- **B-02 — evidência de compra/pontos/impacto:** somente se as estruturas existentes não puderem representar vínculo, unicidade, auditoria e versão da regra.
- **B-03 — referência de mídia:** somente se não houver campo/relação adequado.

Esses itens não autorizam tabelas novas automaticamente. Cada necessidade terá contrato, migration revisada, teste sobre a versão real, plano de compatibilidade e implantação pelo responsável. Não rodar instalador completo sobre banco existente, não apagar campos/dados nem contornar RLS/proteção para fazer uma tela funcionar.

## 14. Ordem prática e trabalho que pode avançar independentemente

1. Organizar a base existente e revisar PR-01/02.
2. Fechar D01–D03 e executar PR-03/04. PR-05 pode avançar independentemente da fórmula de pontos e do armazenamento de fotos.
3. Fechar D04/D05 e preparar PR-06/07. O aceite completo dos avisos depende de PR-20; não confundir notificação local com distribuição global pronta.
4. Fechar D06–D08 e executar PR-08 → PR-09 → PR-10 → PR-11; PR-20 depende da pontuação oficial e de D13, integrando o aceite de proximidade.
5. Perfil, mídia e assistente podem avançar após seus próprios contratos, sem bloquear a vitrine geográfica. Não precisam virar uma stack única de 19 branches.
6. Homologar cada etapa e finalizar PR-19 quando necessário.

**Próxima unidade de código mais independente:** PR-05, ajuste do destino Google Maps, depois de revisar a base. **Maior prioridade de contrato:** PR-03, porque o feed por proximidade é o núcleo da vitrine. **Maior bloqueio de produto:** comprovar compras e definir a pontuação antes de completar impacto.

## 15. Responsabilidades e abertura de PR

| Responsável | Ação |
| --- | --- |
| Isabella/produto | Responder decisões de raio, notificação, compra, pontos, impacto e prioridades; confirmar cada envio |
| Desenvolvimento Android | Implementar apenas contra contratos acordados, testar lógica e estados, preparar diffs pequenos |
| Equipe API/banco | Validar contratos, persistência, titularidade, transações e migrações; publicar versões compatíveis |
| Responsável mercado/integração | Definir e operar a confirmação de compra e disponibilidade das ofertas |
| Infraestrutura/provedores | Entregar URLs, HTTPS, dados de teste e armazenamento autorizado, sem segredos em PR |
| Isabella/QA | Executar Android Studio/aparelho, incluindo cenários de localização e background |

Para cada entrega:

1. Conferir se a mudança já existe em PR/branch/main e atualizar a base por procedimento seguro.
2. Apresentar escopo, repositório, dependências, testes e o que fica de fora.
3. Implementar e validar localmente, preservando alterações de terceiros.
4. Preparar 1–3 commits com `<type>(<scope>): <subject>`; usar `feat/` ou `fix/`, nunca `codex/`.
5. **Pedir confirmação antes de push/PR.** O push também precisa de confirmação quando aciona o bot.
6. Após autorização, fazer push e deixar o bot abrir PR onde esse fluxo existir. Onde não houver bot, confirmar separadamente a abertura manual.
7. Preencher descrição no padrão: O que muda / Por que / Como testar / Checklist / Issues / Screenshots, com dependências e evidências reais.
8. Merge somente depois de review e aceite autorizados. Não alterar ambiente/provedor/banco por consequência automática de publicar uma branch.

## 16. Critério geral de pronto e limites desta versão

Uma entrega está pronta quando: contrato compatível publicado, implementação revisada, teste automatizado pertinente aprovado, UI/integração validadas quando aplicáveis, erros e permissões tratados, documentação atualizada e ausência de segredos verificada. A coluna “código existe” não basta.

Este plano não inclui compra online, pagamento, reserva, cashback, descontos por pontos, resgates, modo visitante ou offline de negócio. Categoria e outras funções antigas não confirmadas precisam de decisão de escopo e contrato antes de gerar PR adicional. Não remover partes existentes silenciosamente em nome do MVP.

O plano ainda não estima uma data final: decisões, ambiente e compra comprovada são dependências externas. Priorizar entregas verticais verificáveis, sem prometer que todo o app esteja completo apenas porque todas as telas abrem.

## 17. Evidências e referências

- [Documentação de produto e arquitetura](../MOBILE-CLIENTE.md).
- [Estado histórico das entregas](delivery-status.md) e [contratos pendentes](remaining-contracts.md).
- Consulta GitHub somente leitura em 20/10/2026: stack do Cliente #10–#18 aberta, #10 draft; API #60 aberta; nome atual da API confirmado pelo GitHub.
- Consulta estrutural em nível dirigido: índice de 13/10, com arquivos alterados/não rastreados pelo índice; os contratos materiais do Android e serviços pertinentes foram lidos diretamente. Não se trata de auditoria exaustiva de todos os repositórios nem de verificação da implantação.
- [Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started): opção de abrir Maps no app ou navegador com destino explícito.
- [Geofencing Android](https://developer.android.com/develop/sensors-and-location/location/geofencing): transições, permissões, restrições e limite de regiões; não permite prometer aviso instantâneo em toda condição.
- [Permissão de notificações Android](https://developer.android.com/develop/ui/compose/notifications/notification-permission): considerar `POST_NOTIFICATIONS` nas versões aplicáveis, independentemente de a interface do projeto usar XML.

Nenhuma PR, push, merge, alteração de código ou migration foi executada para criar este plano. A publicação anterior do guia no Hub não é autorização permanente para enviar os próximos arquivos.
