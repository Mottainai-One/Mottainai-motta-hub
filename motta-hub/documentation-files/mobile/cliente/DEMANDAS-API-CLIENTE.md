# Demandas do Mobile Cliente para a equipe da API

> Alinhamento de 21/10/2026. Documento para encaminhar à pessoa responsável pela API Cliente. O trabalho desta frente é **somente Android Cliente**: não inclui implementar API, PDV, IA, migrations, implantação ou configurar serviços externos. Este documento não declara endpoints novos publicados nem autoriza PR/push.

## 1. Como trabalhar em conjunto

- A API Cliente é responsabilidade de outra pessoa. O mobile entrega requisitos, adapta DTOs/telas e testa contra contratos publicados; não implementa servidores para contornar dependências.
- As rotas abaixo são as que o Android já consome, originalmente atendidas pela API SQL existente. A pessoa responsável decide como reaproveitar/migrar internamente. Se o endereço ou contrato mudar, informar a diferença antes da integração.
- Para cada entrega: enviar método/rota, autenticação, parâmetros, exemplos JSON, códigos de erro, datas/fuso, limites e URL de ambiente. Preferência por OpenAPI versionado e exemplos reproduzíveis.
- Não precisamos de credenciais SQL, segredo Cloudinary, chave de modelo ou service account Firebase no Android/Git. Configuração privada fica no servidor.

## 2. Regras confirmadas de produto

| Área | Regra |
| --- | --- |
| Identidade | Firebase Authentication por senha e Google; Firebase somente autenticação |
| Cadastro e negócio | Perfil e dados persistidos por API/SQL, não Firestore |
| Acesso | Serviços após conta/perfil válido e localização autorizada/ativada |
| Vitrine | Compra somente no mercado; sem checkout, pagamento ou reserva no Cliente |
| Geografia | Posição atual do aparelho; raio 5/10/15/20 km, padrão 5, selecionado na confirmação do endereço |
| Ordenação | Mais perto primeiro; depois maior desconto percentual. Não ordenar primeiro por economia em reais |
| Lojas/ofertas | Somente parceiros Mottainai e conteúdo elegível/disponível |
| Avisos | Mesmo raio das ofertas, inclusive em segundo plano; sem internet não emitir |
| Limite | Cada loja pode emitir até 3 avisos de produtos diferentes por dia; deduplicar para cada destinatário |
| Fidelidade | 1 ponto por real sobre o total efetivamente gasto na compra, comprovado pelo PDV |
| Identificação da compra | CPF, resolvido com segurança no backend; não é senha nem autorização |
| Cancelamento/devolução | Retirar os pontos concedidos, com histórico auditável |
| Benefício | Quem tem mais pontos recebe primeiro as melhores promoções/lotes menores; demais recebem depois |
| Impacto | Status de participação baseado na fidelidade; não converter dinheiro/pontos em kg/CO₂ sem metodologia |
| Fotos | Avatar somente Cloudinary; produto via API externa, oferta usa foto do produto |
| Offline | Sem funcionamento offline de negócio no Cliente |

A regra de 1 ponto/real substitui a hipótese antiga de bônus para produtos promocionais. Não criar multiplicador sem nova decisão.

## 3. Autenticação e perfil — prioridade inicial

### Contrato já consumido

O app envia `Authorization: Bearer <Firebase ID token>`. Validar assinatura, expiração e projeto/issuer/audience corretos; obter UID do token verificado. Não confiar em UID, papel ou customerId arbitrário enviado pelo consumidor. Não exigir login de funcionário ou JWT legado para acessar essas rotas.

| Método | Rota atual | Uso |
| --- | --- | --- |
| GET | `/api/v1/client/auth/profile` | Perfil próprio, vínculo UID → cliente SQL |
| POST | `/api/v1/client/auth/profile` | Criar/concluir perfil da conta autenticada |
| PUT | `/api/v1/client/auth/profile` | Editar perfil próprio |

POST já enviado pelo app, com valores fictícios ilustrativos:

```json
{
  "fullName": "Cliente de Teste",
  "cpf": "<CPF válido do ambiente de testes>",
  "phone": "<telefone de teste>",
  "birthDate": "2000-01-15",
  "marketingConsent": false,
  "address": {
    "zipCode": "<8 dígitos>",
    "street": "Rua de Teste",
    "number": "100",
    "complement": "",
    "neighborhood": "Centro",
    "city": "São Paulo",
    "state": "SP"
  }
}
```

Não há senha no POST SQL. O e-mail de acesso pertence à identidade Firebase verificada. O contrato atual permite nascimento nulo; confirmar obrigatoriedade/tipos antes de mudar o formulário.

Resposta mínima necessária ao acesso, atualmente consumida:

```json
{"id": 7, "birthYear": 2000, "active": true, "marketingConsent": false}
```

- GET: `200` com ID válido e `active` explícito; `404` somente para conta autenticada sem perfil. `403`, `500` ou falha de rede não significam cadastro ausente.
- POST: confirmar `201` com perfil; criação idempotente por identidade, inclusive retry após resultado desconhecido. Documentar `409` e recuperação do perfil já criado, sem duplicar cliente.
- PUT atual envia `fullName`, `phone` e `marketingConsent`. Omitido/null deve preservar telefone; definir separadamente a remoção explícita. Não apagar telefone ao editar nome/consentimento.
- Atual resposta protegida não fornece nome/contato legível. Precisamos de representação autorizada do perfil próprio para recuperar nome após novo login, contato permitido e preferências. **Não devolver hashes como se fossem nome/e-mail/telefone**, nem presumir reversibilidade de hash.
- Precisamos ler/gravar o raio selecionado junto às preferências oficiais. Publicar campo/tipo/rota e comportamento de criação/atualização; sugestão de nome `offerRadiusKm`, ainda não adotada no Android. Só aceitar 5/10/15/20 e retornar padrão 5 quando aplicável.
- Validar titularidade, conta inativa, unicidade e troca de identidade. Não associar CPF/UID de outra pessoa automaticamente por coincidência de e-mail.

## 4. Catálogo geográfico — prioridade seguinte

### Rotas já consumidas

| Rota GET | Parâmetros atuais |
| --- | --- |
| `/api/v1/customer-catalog/stores` | `page`, `size`, `query`, `latitude`, `longitude`, `radiusKm` |
| `/api/v1/customer-catalog/stores/{id}` | ID da unidade |
| `/api/v1/customer-catalog/promotions` | `page`, `size`, `query`, `storeId` |
| `/api/v1/customer-catalog/promotions/{id}` | ID da promoção |

Essas rotas também precisam aceitar Firebase consumidor, sem conceder acesso às rotas operacionais. Perfil e catálogo devem funcionar com a mesma identidade.

### Extensão necessária

- Promoções precisam receber latitude/longitude/raio ou contrato equivalente. Sugestão: manter os mesmos nomes de parâmetros das lojas, a confirmar pela API.
- Filtrar elegibilidade e proximidade **antes de paginar**, com distância crescente, desconto percentual decrescente e desempate determinístico. Retornar distância/unidade do cálculo e percentual utilizado na ordenação para o mobile não reconstruir uma ordem diferente.
- Não devolver páginas globais para o Android filtrar depois: perderia ofertas próximas e invalidaria a paginação.
- Excluir promoção não aprovada, inativa, fora de vigência, indisponível ou de loja inativa/não parceira. Aplicar regras coerentes no detalhe, revalidado após toque no aviso.
- Em busca geográfica, loja sem coordenadas não pode ser anunciada como próxima. Se existir consulta geral para outros consumidores, ausência de coordenadas não deve excluir essa loja indiscriminadamente dessa consulta geral.
- Sem itens próximos: página vazia válida, sem ampliar raio automaticamente. Documentar limite do raio, combinações incompletas/inválidas e respostas `400`.
- Preço original ausente/zero: não inventar desconto nem dividir por zero. Em promoções com vários itens, definir como o percentual de ordenação representa o conjunto; não assumir regra silenciosa.

### Campos atuais e lacunas

Loja consumida: `id`, `name`, `latitude`, `longitude`, `address` com `zipCode`, `street`, `number`, `complement`, `neighborhood`, `city`, `state`. Precisamos identificar a **unidade**, não apenas a rede, para abrir o Google Maps corretamente.

Promoção consumida: `id`, `name`, `description`, `promotionType`, `startsAt`, `endsAt`, `store`, `items`. Cada item contém `id`, `productId`, `name`, `originalPrice`, `promotionalPrice`, `quantityAvailable`. Complementar referência de imagem e identificação GTIN quando apropriado; mobile não possui GTIN no DTO atual.

Paginação atual é indexada em zero: `content`, `number`, `size`, `totalElements`, `totalPages`. O Android pede tamanho 20. Preservar ou documentar mudança, limite máximo e ordenação estável. IDs precisam ter formato consistente entre catálogo, detalhe e avisos.

## 5. Compra, pontos e status — integração externa ao mobile

Rotas atualmente consumidas:

- `GET /api/v1/client/loyalty/balance`: `id`, `customerId`, `pointsBalance` (hoje inteiro no Android).
- `GET /api/v1/client/loyalty/transactions?from=...&to=...`: lista com `id`, `transactionType`, `points`, `description`, `createdAt`.
- Histórico atual usa janelas mensais inclusivas e período máximo de seis meses, com precisão de microssegundos. Confirmar compatibilidade e fuso; app adapta se o novo contrato mudar.

Necessidades do servidor:

1. Receber venda confirmada e estornos do PDV por integração autenticada, vinculando CPF ao cliente correto, loja, itens e venda única.
2. Calcular 1 ponto por real sobre total gasto; não aceitar crédito declarado pelo consumidor. Clique/rota/proximidade não comprovam compra.
3. Garantir transação, idempotência e concorrência: mesma venda não credita duas vezes; mesma devolução não debita duas vezes. Preservar relação de crédito/estorno e tratar devolução parcial.
4. Publicar saldo/histórico e status oficial. Android só apresenta; não calcula pontuação, prioridade ou nível como autoridade.
5. Definir centavos antes de publicar DTO: pontos fracionados exigem alterar o tipo inteiro atual no app; não arredondar por acidente no JSON. Definir venda com CPF ainda não cadastrado e eventual vínculo posterior, sem cadastro automático presumido.

Faixas iniciais propostas para participação Mottainai: **Semente [0,100), Broto [100,500), Planta [500,1500), Árvore [1500,3000), Floresta [3000,+∞)**. Não são certificação ambiental; publicar nível, pontos válidos e próximo marco calculados no servidor. Período/expiração precisam de decisão explícita. CPF não deve ser exposto em histórico/notificação ou em rota pública de busca.

## 6. Avisos próximos e prioridade por fidelidade

O mobile cuidará das permissões Android, canais, geofencing e exibição local, inclusive segundo plano. Precisamos do contrato de **conteúdo elegível e autorização de emissão** do servidor; geofencing sozinho não determina prioridade global entre clientes.

- Registrar/consultar preferência oficial de raio e ativação dos avisos, sem confundir marketingConsent, permissão Android e preferência de notificações.
- Fornecer regiões de parceiros elegíveis com coordenadas, identificação e validade; permitir seleção/renovação limitada às regiões relevantes, sem tentar registrar todo o país.
- Autorizar no máximo três campanhas/avisos de produtos distintos por loja/dia, com fuso declarado. Uma campanha pode alcançar seus destinatários; não confundir limite de campanhas com três destinatários totais. Impedir repetição para a mesma conta, inclusive em aparelhos diferentes.
- Liberar melhores ofertas primeiro aos clientes com mais pontos e depois aos demais. **Faltam duração da antecedência, definição do primeiro grupo e empate**; equipe/produto precisam acordar antes de codificar. Não transformar prioridade de comunicação em reserva ou exclusividade no catálogo sem aprovação.
- Na transição geográfica, o Android reconsulta disponibilidade e elegibilidade online. Sem conexão, não emite. Precisamos definir comportamento de autorização, deduplicação, expiração e confirmação de emissão sem consumir quotas silenciosamente por retry.
- Payload sugerido para acordar, não contrato já implementado: identificador único de aviso, loja, produto, promoção, título/texto, instante de liberação e expiração. O toque abre conteúdo revalidado; destinatário deve vir da identidade autenticada, não de ID arbitrário.
- Não colocar CPF/token/dados privados no conteúdo visível. Logout/troca de conta deve invalidar trabalho pendente do destinatário anterior.
- “Liberar primeiro” no servidor é verificável; recebimento/visualização instantânea não é garantido pelo Android. Informar como tratar queda de estoque/expiração durante a janela prioritária.

Não adicionar FCM por suposição: Firebase foi limitado à autenticação. Se a arquitetura exigir transporte de push remoto, trazer proposta explícita para aprovação; não trocar silenciosamente o escopo.

## 7. Avatar e imagens dos produtos

### Campos opcionais preparados no Android (proposta, ainda não publicados)

- No saldo: `statusName: string | null` e `pointsToNextStatus: integer | null`. São valores calculados pelo servidor; ausência não impede mostrar o saldo e não produz nível local. Confirmar se esses nomes/tipos serão adotados.
- No catálogo/detalhe: `imageUrl: string | null` como referência explícita da promoção/produto e `items[].imageUrl: string | null`. O Android usa a referência de um item apenas se houver um único produto; promoções com vários itens precisam de capa explícita, sem escolher foto arbitrária.
- Imagens são URLs públicas HTTPS, sem credenciais embutidas, tokens de autenticação ou dependência de headers Firebase. Validar provedor/licença/atribuição antes de publicar. Falta de imagem mantém placeholder; não bloqueia a oferta.

### Avatar Cloudinary

Precisamos de upload autorizado, limites tipo/tamanho, confirmação da referência no perfil, leitura posterior, substituição e exclusão. Assinaturas/segredos ficam no backend; Android não recebe o secret do Cloudinary. Validar que o arquivo confirmado pertence ao cliente, sem permitir referência arbitrária de outra conta.

Publicar o fluxo e formato antes de integrar o seletor Android. URI local de arquivo não é avatar persistido. Não precisamos de Firebase Storage nem Base64 no cadastro SQL.

### Produto/oferta

Recomendação para piloto: **Open Food Facts**, consulta por GTIN e referência de imagem frontal. A oferta usa a foto do produto; falta de foto usa placeholder. O provedor não define preço, estoque, desconto ou validade da loja.

A equipe da API deve validar cobertura com GTINs reais, versão suportada, atribuição/licenças e limites; Open Food Facts não é garantia de foto para todo item. Cosmos/Bluesoft é alternativa a avaliar, não uma segunda integração obrigatória. Não enviar dados pessoais a esses provedores.

Publicar campo de imagem, fonte/atribuição quando necessária e comportamento de indisponibilidade. O mobile consome a referência aprovada, sem scraping, foto parecida pelo nome ou segredo de provedor no APK. Cloudinary continua exclusivo para avatar neste escopo.

## 8. Assistente existente da IA

O Android já implementa os contratos observados de envio, histórico e lista de conversas, condicionado à configuração `MOTTAINAI_ASSISTANT_BASE_URL`. Isso não certifica suporte ao consumidor no servidor.

- `GET /chat/history/{session_id}`: `{session_id, status, messages:[{role,content}]}`; apresenta apenas user/assistant e valida o ID da conversa. `404` não provoca reenvio automático.
- `GET /chat/sessions`: `{sessions:[{sessionId,title,status,lastInteraction}]}`; a lista usa camelCase, diferente do envio/histórico.
- `POST /chat`: mensagem de até 4096 caracteres, ID até 128 conforme expressão do serviço; nenhum papel/empresa é enviado.
- O token Firebase identifica a conta; não há segredo de LLM. Falha de autorização exclusiva da IA não apaga a sessão SQL.
- Histórico/conversa corrente ficam só na memória do Android; histórico persistido é consultado pela API da IA. Rotação preserva a conversa via ViewModel, encerramento do processo não grava transcrição em disco.

Há agente consumidor na IA, não precisamos reconstruí-lo no Android. O contrato observado é `POST /chat` com `message` e `session_id`; campos extras são rejeitados. A resposta observada inclui `session_id`, `response`, `agent`, `judge_approved`, `judge_score`, `sources`, `latency_s`; publicar tipagem/nulabilidade, histórico e erros da versão que será integrada.

O resolvedor Firebase examinado na IA ainda atendia funcionário. Equipes API/IA precisam entregar identidade de consumidor válida e sessões/histórico por titular, sem inventar empresa/cargo ou confiar em role/clientId enviados pelo app. Definir se a chamada será direta à IA ou mediada pela API, URL e autenticação correspondentes. Não precisamos de chave de LLM no Android nem respostas locais fictícias para conta real.

## 9. Erros, datas e ambiente

- `401`: token ausente/inválido/expirado. O Android já limita refresh/repetição; não usar `401` para indisponibilidade do serviço.
- `403`: autenticado sem permissão/inativo conforme contrato, sem revelar dados de terceiros.
- `404`: distinguir perfil inexistente de recurso removido/inelegível no contexto da rota.
- `400/409/422/429`: documentar validação, conflito, limite e retry; padronizar corpo de erro estável sem stack trace, CPF ou token.
- `5xx`/rede: recuperável; não pedir criação de outra conta para corrigir falha transitória.
- Datas de cadastro `YYYY-MM-DD`; instantes, fuso/offset e limites de vigência precisam estar documentados. Histórico atual usa LocalDateTime sem offset; mudança deve ser combinada, não reinterpretada silenciosamente.
- Entregar URL HTTPS acessível e dados de teste controlados: cliente ativo/inativo/sem perfil, duas contas, parceiros dentro/fora do raio, ofertas inelegíveis e compra/estorno de teste.
- A configuração Android usa `MOTTAINAI_API_BASE_URL`; novo endereço deve ser informado, não exige credenciais do servidor no APK.

## 10. Ordem sugerida das entregas externas

1. Firebase consumidor + perfil próprio/cadastro idempotente + leitura autorizada/preferência de raio.
2. Catálogo geográfico paginado e ordenado, detalhes e referências de imagens.
3. PDV → compra/CPF → crédito/estorno → saldo/histórico/status.
4. Elegibilidade de avisos, quota e liberação prioritária, coordenadas/validade de regiões.
5. Avatar Cloudinary e autorização consumidor para IA, em paralelo conforme disponibilidade.

Cada entrega deve poder ser integrada isoladamente. O mobile continua com carregamento/vazio/erro reais; “tela abre” não comprova contrato publicado.

## 11. Checklist para devolver ao responsável Android

- [ ] URL, versão/commit e OpenAPI do ambiente.
- [ ] Login Firebase senha/Google → perfil e catálogo funcionando com a mesma conta.
- [ ] Exemplos de request/response e erros, sem dados reais ou segredos.
- [ ] Campos/tipos definitivos para raio, distâncias, percentual, imagem e pontos.
- [ ] Testes de titularidade entre contas, perfil inativo e separação consumidor/funcionário.
- [ ] Paginação/filtros e exclusão de ofertas inelegíveis antes da paginação.
- [ ] Venda/estorno idempotentes e exemplos com centavos/devolução parcial.
- [ ] Decisões de janela/grupo prioritário, fuso diário e deduplicação dos avisos.
- [ ] Upload/avatar e acesso IA publicados quando forem liberados para integração.

## Referências

- [Contrato atual de autenticação do Android](authentication.md).
- [Catálogo e testes](catalog.md), [acesso por localização](location-access.md).
- [Open Food Facts — API, limites e licenças](https://openfoodfacts.github.io/openfoodfacts-server/api/).
- [Cosmos — API](https://api.cosmos.bluesoft.com.br/api) e [licenças por item](https://api.cosmos.bluesoft.com.br/licenses).

Este MD descreve demandas e propostas, não implementa nem afirma que o backend novo já atende a elas. Aprovação de PR/push continua separada e depende de Isabella.
