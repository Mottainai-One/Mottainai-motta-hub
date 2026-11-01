# Mottainai Mobile Cliente — documentação funcional e técnica

> Atualização: **21/10/2026**. Este documento reúne o estado observado no código local, as decisões recentes do projeto e as pendências para entrega. **Implementado no Android não significa publicado na API nem validado ponta a ponta.** A entrega local `fix/firebase-auth-only` não foi enviada nem teve PR aberta.

> Publicação documental no Mottainai Hub; código Android, serviços e homologação não são publicados por este envio.

## Decisões consolidadas em 21/10/2026

Estado local mais recente: autenticação/perfil, acesso por localização, lojas compartilhadas entre Home/mapa, raios, destino Google Maps, consulta de pontos, Impacto por saldo, cliente HTTP do assistente e carregamento opcional de imagens implementados no Android. 63 testes JVM e 60 XMLs analisados; sem build APK/lint/UI. Contratos externos e homologação permanecem pendentes; o envio desta documentação não publica o código Android.

- Raios **5, 10, 15 e 20 km**, padrão **5 km**, selecionados ao confirmar o endereço. A proximidade usa a posição atual do aparelho, não presume que ele esteja no endereço cadastrado.
- Localização obrigatória para os serviços do app: recusa bloqueia esses recursos. Manter entrada, recuperação da conta e orientação para conceder permissão acessíveis; o app real bloqueia serviços sem localização, sem substituir por lista geral.
- Avisos usam o mesmo raio das ofertas, somente para lojas parceiras Mottainai. Sem internet, não emitir aviso nem afirmar disponibilidade com dados antigos.
- Cada loja poderá emitir **três avisos por dia, de produtos diferentes**, com funcionamento em **segundo plano**. Quota de campanhas da loja, deduplicação por destinatário e fuso precisam constar no contrato; não tratar como apenas três destinatários por dia. Respeitar permissões/restrições Android, sem garantia de entrega imediata ou após force-stop.
- O **PDV Mottainai** comprova a compra e identifica o cliente pelo **CPF**. O crédito será de **1 ponto por real gasto**, calculado no backend, com contrato autenticado de confirmação/estorno. Falta definir centavos e base elegível. Essa fórmula substitui a hipótese anterior de bônus para produtos promocionais.
- Pontos são de **fidelidade**: clientes com maior pontuação recebem prioritariamente comunicações de melhores promoções/lotes menores. Isso substitui a decisão anterior de pontos exclusivos para impacto. Não autoriza reserva, exclusividade no catálogo, desconto por troca de pontos ou cashback.
- Cancelamento/devolução retira os pontos ganhos na compra. O backend precisa registrar estorno auditável e idempotente; devolução parcial e fórmula ainda exigem definição.
- Impacto será apresentado como jornada/status de participação por fidelidade, não certificação ambiental. Faixas propostas e pesquisa estão em [Fidelidade e imagens](cliente/FIDELIDADE-E-IMAGENS.md): Semente, Broto, Planta, Árvore e Floresta. Valores são desenho inicial do programa, não medida científica; período/expiração ainda precisam de validação.
- Cadastro mantém os campos do contrato/banco existente. Para imagens, recomenda-se piloto com **Open Food Facts**, validando cobertura por GTIN e termos antes de produção; a oferta usa a imagem do produto. Avatar **somente no Cloudinary**. A pesquisa compara Cosmos como alternativa, sem integrar dois provedores por antecipação.
- Reutilizar o assistente de cliente da IA. Em `main` da IA (`021fdc0`), há agente consumidor RAG, mas o resolvedor de identidade Firebase examinado ainda resolve funcionário, não cliente; agente existente não significa integração Android autorizada.

Verificações dirigidas de repositórios em 21/10: `main` de [API Cliente](https://github.com/Mottainai-One/Mottainai-Api-SQL-Cliente) contém apenas `LICENSE`; existem outras branches, não auditadas. Os contratos consumidos hoje estão na API SQL Operacional. Definir com a equipe onde evoluir/reutilizar esses contratos, sem duplicar serviços por suposição. No [POS](https://github.com/Mottainai-One/Mottainai-POS), o caminho de venda examinado em `main` usa `MockApiService`; o modelo de venda possui vínculo opcional de cliente, mas isso não comprova integração real com pontos. Outras branches e ambiente publicado não foram homologados.

Plano inicial histórico: [plano de implementação](cliente/PLANO-IMPLEMENTACAO.md). Para execução vigente somente Android, usar [plano mobile atualizado](cliente/PLANO-MOBILE-CLIENTE.md) e [pesquisa de fidelidade/imagens](cliente/FIDELIDADE-E-IMAGENS.md). Esta consolidação substitui perguntas históricas abaixo sobre opções de raio, background, CPF e fórmula; não aplicar o bônus promocional anteriormente cogitado. Descrições de código atual não representam aceite dessas novas regras.

## Índice

Escopo confirmado: esta frente cuida **somente do Android Cliente**. Backend é responsabilidade de outra pessoa; consulte o [plano mobile atualizado](cliente/PLANO-MOBILE-CLIENTE.md) e o [MD para a equipe da API](cliente/DEMANDAS-API-CLIENTE.md). Entregas backend de planos anteriores são dependências externas, não autorização para implementá-las aqui.

Atualização local de 21/10: [acesso por sessão/localização](cliente/location-access.md). Main, detalhe e assistente exigem localização no uso real; Home e Lojas compartilham raio/posição, com leitura automática em primeiro plano e atualização manual. Raio 5/10/15/20 km, padrão 5. O feed de promoções geográfico e as notificações ainda não estão implementados; descrições anteriores de permissão opcional/lista geral foram substituídas por esse fluxo.

1. [Objetivo e público](#1-objetivo-e-público)
2. [Decisões e limites](#2-decisões-e-limites)
3. [Estado das funcionalidades](#3-estado-das-funcionalidades)
4. [Arquitetura](#4-arquitetura)
5. [Estrutura do projeto](#5-estrutura-do-projeto)
6. [Persistência e origem dos dados](#6-persistência-e-origem-dos-dados)
7. [Autenticação e sessão](#7-autenticação-e-sessão)
8. [Cadastro e endereço](#8-cadastro-e-endereço)
9. [Home](#9-home)
10. [Catálogo e detalhe de oferta](#10-catálogo-e-detalhe-de-oferta)
11. [Lojas, localização e mapa](#11-lojas-localização-e-mapa)
12. [Pontos e histórico](#12-pontos-e-histórico)
13. [Perfil e avatar](#13-perfil-e-avatar)
14. [Impacto ambiental](#14-impacto-ambiental)
15. [Assistente](#15-assistente)
16. [Notificações e geofencing](#16-notificações-e-geofencing)
17. [Contratos HTTP](#17-contratos-http)
18. [Erros, concorrência e conectividade](#18-erros-concorrência-e-conectividade)
19. [Segurança e proteção de dados](#19-segurança-e-proteção-de-dados)
20. [Configuração do ambiente](#20-configuração-do-ambiente)
21. [Testes e critérios de aceite](#21-testes-e-critérios-de-aceite)
22. [Pendências e sequência de implementação](#22-pendências-e-sequência-de-implementação)
23. [Branches, commits e PRs](#23-branches-commits-e-prs)
24. [Diagnóstico de problemas](#24-diagnóstico-de-problemas)
25. [Referências e manutenção](#25-referências-e-manutenção)
26. [Alinhamento de produto e decisões em aberto](#26-alinhamento-de-produto-e-decisões-em-aberto)

## 1. Objetivo e público

O Cliente é o aplicativo Android para consumidores do ecossistema Mottainai. Permite encontrar promoções, consultar lojas e acompanhar os pontos registrados pelo sistema, apoiando a redução do desperdício.

Não é o aplicativo de gestão de estoque. Cadastro de produtos, movimentações, inventário físico, aprovação operacional e gestão de funcionários pertencem ao Operacional e aos serviços administrativos.

A relação esperada entre os dois apps é: uma ação operacional válida altera os dados oficiais; a API aplica as regras de publicação; o Cliente consulta o catálogo permitido. Não se deve copiar esse catálogo para um banco Firebase paralelo. A atualização depende de nova consulta e do processamento no backend; não há garantia de atualização instantânea na tela.

## 2. Decisões e limites

### 2.1 Decisões confirmadas

- **Firebase somente para autenticação.** Não usar Firestore, Realtime Database, Firebase Storage ou outros produtos Firebase para persistir dados de negócio.
- **Acesso autenticado obrigatório:** os serviços do app, incluindo ofertas e mapa, só ficam disponíveis após criar conta/concluir o perfil necessário ou fazer login. Não haverá exploração de serviços como visitante. Demonstração debug é ferramenta de teste, não exceção em produção.
- **Aplicativo-vitrine:** a compra é realizada exclusivamente no mercado. O Cliente apresenta ofertas e direciona à unidade, sem compra, pagamento ou checkout pelo app.
- **Offline é exclusivo do Operacional.** O Cliente não terá catálogo, perfil ou pontos persistidos para navegação offline.
- **Google Maps permanece como serviço de mapa.** Google Maps não implica usar Firebase como banco.
- **Descoberta de ofertas por proximidade:** o mapa deve localizar mercados próximos à posição atual do cliente, e as promoções apresentadas devem corresponder aos mercados próximos e às ofertas disponíveis.
- **Prioridade de ordenação:** primeiro os mercados mais próximos; dentro dessa prioridade, ofertas com maiores descontos **percentuais**, não maior valor economizado em reais. Segundo a regra de negócio informada, os maiores descontos já correspondem aos produtos mais próximos do vencimento; não adicionar uma ordenação independente por validade que se sobreponha à distância/desconto.
- **Finalidade exclusiva dos pontos no MVP:** pontos obtidos na compra de produtos serão usados somente para medir o impacto sustentável do cliente. Produtos em promoção dão mais pontos, conforme a regra de produto informada, associada à economia. Não haverá cashback, troca por descontos, cupons ou resgate de recompensas nesse MVP. Comprovação da compra, fórmula de concessão e conversão em métricas ainda precisam de contrato.
- **Destino da oferta:** o detalhe deve ter um botão “Como chegar” que abra o app oficial Google Maps ou seu site, com a unidade exata que anunciou a promoção marcada como destino.
- **Aviso de proximidade:** ao passar perto de uma loja, o cliente deve poder receber uma notificação de suas ofertas vigentes, conforme permissões e regras de frequência ainda a definir. Isso faz parte do escopo completo, não é apenas um mapa estático.
- O app usa **Java e XML**, preservando a navegação e os componentes existentes.
- Dados de negócio são acessados por APIs. O Android não recebe credenciais nem abre conexão direta com os bancos.
- Senhas e chaves privadas de servidor não são armazenadas pelo código do app.
- Dados demonstrativos só servem a desenvolvimento; não podem simular resultados reais em produção.
- Prompts antigos não prevalecem sobre essas decisões.

### 2.2 Persistência: direção recomendada, não migração concluída

O código já consome a API SQL. A recomendação é manter PostgreSQL como fonte oficial dos dados relacionais, aproveitar a API existente e escolher um serviço de objetos para fotos. A definição final de armazenamento, infraestrutura e proteção deve ser validada pela equipe antes de novos contratos ou migrações.

Não há decisão para introduzir Room no Cliente. Room/cache de negócio offline pertence à discussão do Operacional.

### 2.3 Consequências ainda pendentes

- A dependência de `FirebaseUser.displayName` foi removida do Android. Falta oferecer a leitura autorizada do nome de negócio no backend; enquanto isso, a apresentação é neutra quando o nome não está disponível.
- FCM também é Firebase. Pela restrição atual, não adotar FCM automaticamente. A solução de push está aberta, incluindo a análise de dependências indiretas de fornecedores.
- Login próprio do site e acesso de funcionários não são migrados por esta documentação. Mudanças nesses fluxos exigem trabalho separado.

## 3. Estado das funcionalidades

Legenda: **implementado** = caminho existente no Android; **parcial** = tela ou fluxo com dependências; **pendente** = integração real não concluída. Nenhum desses rótulos substitui o teste em ambiente integrado.

| Funcionalidade | Estado observado | Dependência ou ressalva |
| --- | --- | --- |
| Onboarding e navegação | Implementado | Roteiro de UI em aparelho ainda necessário |
| Login e-mail/senha | Implementado | Firebase e perfil SQL acessíveis |
| Login/cadastro Google | Implementado | Provedor, OAuth e assinatura Android configurados |
| Cadastro em duas etapas | Implementado | Validação e gravação pela API |
| Recuperação de senha | Implementado | Serviço Firebase disponível |
| Retomada de sincronização SQL | Implementado | Mesma identidade Firebase; API compatível |
| Home | Implementado | Consultas independentes de perfil, saldo e catálogo |
| Catálogo e detalhe | Implementado no app | Validar autorização Firebase nas rotas do backend |
| Feed de ofertas dos mercados próximos | Pendente de integração geográfica | Catálogo atual não recebe automaticamente a localização usada na tela de lojas |
| Lojas, pins e rota | Implementado | Coordenadas reais e chave Maps válida |
| Botão do detalhe abrindo Google Maps oficial | Implementado localmente; pendente de teste Android | Auxiliar compartilhado abre pin da unidade no app oficial ou por URL web; 7 testes JVM |
| Busca de lojas por raio | Implementado localmente | 5/10/15/20 km e localização obrigatória; preferência ainda é estado de tela |
| Saldo e histórico de pontos | Implementado | Titularidade e dados existentes no servidor |
| Perfil e edição básica | Parcial | Nome não é gravado/lido no Firebase; falta leitura autorizada pela API |
| Avatar persistido | Pendente | Serviço de arquivos e contrato de autorização |
| Impacto real | Saldo apresentado; status opcional | Nível/progresso calculados pela API; sem conversões ambientais |
| Assistente real | Cliente HTTP implementado | Configuração da URL e homologação da autorização consumidor na IA |
| Push | Pendente | Solução compatível com Firebase somente para Auth |
| Geofencing | Pendente | Regras, permissões e eventos definidos |
| Demonstração em debug | Implementado | Não equivale a integração nem a offline de produção |
| Compra, pagamento e resgate | Fora da entrega atual | Exigem escopo próprio |

## 4. Arquitetura

```text
Activity / Fragment + XML
          |
          v
ViewModel + LiveData
          |
          v
Repository
  |         |                  |
  v         v                  v
Firebase    Retrofit/OkHttp     Dados demonstrativos
Auth        |                  somente em debug
            v
       API do sistema
            |
            v
       Persistência oficial
```

### Responsabilidades

| Camada | Responsabilidade | Não deve fazer |
| --- | --- | --- |
| Activity/Fragment | Eventos, navegação e renderização de estado | Consultar SQL ou calcular regras de pontos |
| ViewModel | Estado da tela, filtros, requisições e resultados | Tratar dados em memória como persistência permanente |
| Repository | Coordenar as fontes e converter sucesso/erro | Inventar sucesso quando o servidor falhou |
| Serviços Retrofit/DTOs | Descrever o contrato HTTP | Receber credenciais de infraestrutura |
| `ApiClient` | Token Firebase, timeouts e recuperação limitada de `401` | Manter repetição infinita de login |
| Backend | Validar identidade, titularidade, regras e transações | Confiar em papel/cliente enviados livremente pelo Android |

O uso de ViewModel pode preservar dados durante recriação da tela. Isso é memória do processo, não base offline nem garantia de recuperação após o Android encerrar o processo.

## 5. Estrutura do projeto

Identificação conferida em `app/build.gradle.kts`:

| Item | Valor do checkout |
| --- | --- |
| Namespace e application ID | `com.mottainai.cliente` |
| `minSdk` | 26 |
| `compileSdk` / `targetSdk` | 36 / 36 |
| Compatibilidade do código Java | 11 |
| Interface | XML, Material Components e ViewBinding habilitado |
| Estado | ViewModel e LiveData |
| Rede | Retrofit, Gson e OkHttp |
| Google Sign-In | Credential Manager e Google ID, integrados ao Firebase Auth |
| Mapa | Maps SDK for Android |

Compatibilidade Java 11 das fontes não determina sozinha o JDK que executa Gradle. Usar a configuração compatível com o Android Gradle Plugin e o CI do projeto; não resolver falhas trocando versões aleatoriamente.

Estrutura principal, relativa à raiz do repositório:

```text
app/src/main/
  AndroidManifest.xml
  java/com/mottainai/cliente/
    MainActivity.java
    activities/        entrada, cadastro, detalhe e assistente
    fragments/         Home, catálogo, lojas, pontos, impacto e perfil
    adapters/          apresentação de listas
    models/            modelos usados na interface
    network/           clientes HTTP e contratos
      dto/             requests e responses
    repository/        acesso às fontes, estados e demonstração
    utils/             sessão e auxiliares
    viewmodel/         estado e coordenação das telas
  res/
    layout/            telas e componentes XML
    navigation/        nav_graph.xml
    values/            textos, estilos, cores e dimensões
    xml/               regras de backup
app/src/test/          testes JVM
.github/workflows/     CI
docs/                  contratos, testes e histórico de entrega
```

Arquivos centrais:

- `AuthRepository`: Firebase, sincronização de perfil e ViaCEP.
- `AuthViewModel`: estados de autenticação/cadastro e controle de ações simultâneas.
- `SessionManager`: associação local de cliente SQL e UID, onboarding e demonstração.
- `ApiClient`: construção do Retrofit e autenticação de requisições.
- `CatalogRepository` / `CatalogViewModel`: catálogo, lojas, filtros e paginação.
- `CatalogPages`: união ordenada das páginas por ID.
- `LoyaltyRepository` / `LoyaltyViewModel`: saldo e histórico.
- `LoyaltyPeriod`: limites mensais inclusivos.
- `ProfileViewModel`: leitura e gravação do perfil.

Há DTOs e mocks legados no projeto. A existência de um arquivo antigo de login/JWT não significa que ele seja o contrato ativo. A referência de chamadas é a interface Retrofit utilizada pelo Repository atual.

## 6. Persistência e origem dos dados

| Informação | Estado atual | Direção definida/recomendada |
| --- | --- | --- |
| Identidade e credenciais | Firebase Authentication | Manter somente autenticação |
| Estado de autenticação | Administrado pelo SDK Firebase | Não duplicar senha/refresh token nas preferências |
| ID SQL e UID associado | `SharedPreferences` | Estado mínimo local, nunca autorização oficial |
| Onboarding | `SharedPreferences` | Preferência simples |
| Perfil de negócio | API SQL | Fonte oficial no backend, respeitando dados protegidos |
| Nome/e-mail exibidos | Nome neutro ou confirmado em memória após edição SQL; e-mail de acesso Firebase | Falta leitura oficial autorizada do nome; não persistir no Firebase |
| Catálogo, lojas e pontos | API; respostas mantidas em memória | Sem banco/cache persistente offline no Cliente |
| Avatar/fotos | Sem upload real concluído | Armazenamento de objetos a definir; referência no backend |
| Impacto | Saldo de fidelidade consultado pela API | Status/progresso dependem dos campos oficiais do servidor |
| Chat | Sem integração real do consumidor | Serviço IA autorizado; nunca conexão Android–Mongo |

O arquivo de preferências de sessão é `mottainai_cliente_session.xml`. O projeto o exclui das regras explícitas de backup e transferência. Isso não significa que todo dado de qualquer SDK esteja coberto por essa regra; revisar separadamente ao adicionar armazenamento ou dependências.

Não criar duplicatas de perfis, pontos ou catálogo no Firestore. O Cliente também não recebe conexões PostgreSQL, Mongo ou Redis. Caso esses serviços sejam usados no backend, permanecem internos.

## 7. Autenticação e sessão

### 7.1 Login por senha

1. Validar formato do e-mail e presença da senha na tela.
2. Autenticar com `signInWithEmailAndPassword` no Firebase.
3. Consultar `GET /api/v1/client/auth/profile` com ID token Firebase.
4. Se houver HTTP `200`/`201`, ID SQL positivo e `active=true`, salvar ID SQL junto ao UID autenticado.
5. Abrir a área principal.
6. Se o perfil não existir (`404`), abrir conclusão do cadastro.
7. Em falha de rede/servidor, oferecer nova sincronização sem criar outra conta.

A senha é usada pelo SDK Firebase. Ela não faz parte do payload de criação do perfil SQL.

Perfil sem situação ativa explícita é resposta incompleta; perfil inativo não libera sessão. HTTP `202`/`204`, mesmo com payload inconsistente, não confirma sincronização. Essa validação também é aplicada às respostas de leitura, criação e edição de perfil.

### 7.2 Google

O Credential Manager obtém a credencial Google. O app a usa para autenticar no Firebase e segue exatamente a mesma consulta do perfil SQL. Google fornece identidade, não elimina CPF/endereço nem as regras do cadastro de negócio.

Uma conta existente por outro provedor pode exigir o método original e um fluxo explícito de vinculação. Não tentar fundir contas somente porque o texto do e-mail é igual.

### 7.3 Identidade Firebase sem perfil SQL

Esse é um estado recuperável, não uma conta totalmente funcional. `pendingProfile()` permite retomar. Durante a conclusão, e-mail fica associado à identidade já autenticada e campos de senha ficam ocultos.

Firebase e SQL não participam de uma única transação distribuída. O servidor precisa suportar repetição segura da criação para a mesma identidade. Não apagar automaticamente a conta Firebase em uma falha transitória nem pedir que o usuário recrie a conta.

### 7.4 Sessão local

`SessionManager.isLoggedIn()` exige identidade Firebase presente, UID igual ao salvo, flag de sessão e ID SQL não vazio. `canBrowse()` também aceita demonstração, exclusivamente em debug.

Essa checagem é de navegação. Não prova que a API esteja disponível nem substitui a autorização do servidor. Um FirebaseUser local pode existir sem que uma nova operação online seja possível.

### 7.5 Expiração e logout

`ApiClient` injeta o ID token e, em `401`, tenta renovar/reutilizar um token mais recente com no máximo uma repetição de autenticação. Rejeição persistente limpa a associação SQL e retorna à entrada, preservando a identidade Firebase para recuperação quando aplicável. Identidade Firebase inválida pode provocar saída completa.

Falha de rede não significa senha errada e não deve gerar logout automático. A saída explícita encerra Firebase e associação local. Requisições atrasadas não podem ativar sessão de outro UID.

### 7.6 Recuperação de senha

Usa `sendPasswordResetEmail` no Firebase. Não depende da API SQL. A confirmação deve ser genérica para não revelar a existência de uma conta.

## 8. Cadastro e endereço

### 8.1 Formulário atual

| Etapa | Campos e comportamento |
| --- | --- |
| 1 — Seus dados | Nome, CPF, e-mail, senha/confirmação quando aplicável, telefone, nascimento e consentimento |
| 2 — Endereço | CEP, rua, número, complemento, bairro, cidade e UF |

Validações observadas:

- Nome: obrigatório, até 150 caracteres.
- CPF: 11 dígitos e dígitos verificadores válidos; rejeita sequências repetidas. Isso não consulta situação cadastral nem comprova titularidade. Verificação oficial e vínculo com compra continuam no servidor.
- E-mail: formato e limite de 150 caracteres.
- Senha de nova conta: 8 a 100 caracteres, com confirmação.
- Telefone: obrigatório no formulário atual, até 20 caracteres.
- Nascimento: o formulário atual aceita vazio; quando preenchido, usa `AAAA-MM-DD` e rejeita futuro.
- CEP: 8 dígitos.
- Rua/número/bairro/cidade/UF: validação antes de enviar endereço completo.
- Complemento: opcional, com limite de tamanho.

**Diferença dos prompts antigos:** a data de nascimento não é obrigatória no formulário e DTO Firebase inspecionados. Não documentar exigência antiga como comportamento atual. Se o produto quiser torná-la obrigatória, alinhar tela e backend.

O DTO Firebase da API também aceita telefone opcional, enquanto o formulário exige. A política deve ser harmonizada; validação de tela não substitui validação no servidor.

### 8.2 ViaCEP

Consulta `https://viacep.com.br/ws/{cep}/json/` em cliente separado do cliente autenticado da API. Preenche rua, bairro, cidade e UF; o usuário informa número e pode corrigir o endereço. Falha da consulta permite preenchimento manual. Não enviar token Firebase a esse serviço.

### 8.3 Gravação e retomada

O fluxo cria/reutiliza a identidade Firebase e faz POST do perfil. Só conclui a associação local após confirmar ID válido e perfil ativo. O nome é enviado apenas à API SQL; não existe segunda gravação no perfil Firebase. Uma falha de atualização de display name não pode mais impedir um cadastro SQL confirmado.

A etapa do formulário é restaurada na recriação da tela. Senhas não devem ser incluídas no estado salvo. Isso não garante recuperação completa de todo o formulário após encerramento do processo.

## 9. Home

Combina saudação/perfil, saldo e seções de ofertas/lojas. As consultas não devem ser uma única operação bloqueante: falha no saldo não deve impedir uma lista de ofertas já recebida.

- Exibir carregamento e erro por seção, com tentativa novamente.
- Manter dado anterior em memória quando o estado permitir, sinalizando falha de atualização.
- Direcionar para catálogo, lojas e pontos sem trocar os IDs da navegação.
- Não inventar pontos, impacto, descontos ou distância.
- Não afirmar que a seção está atualizada quando a nova consulta falhou.

**Comportamento de produto confirmado, ainda a integrar:** ofertas da Home devem acompanhar o contexto geográfico dos mercados próximos à localização atual, e não apresentar promoções de qualquer região como se fossem próximas. Priorizar distância crescente e, dentro dessa prioridade, desconto percentual decrescente. Os maiores descontos já refletem a proximidade do vencimento segundo a regra informada pelo produto. Não acrescentar relevância ou vencimento como prioridade acima desses critérios. O compartilhamento do contexto com o Catálogo e o momento de atualização ainda precisam ser definidos na implementação.

## 10. Catálogo e detalhe de oferta

- Consulta promoções com `page`, `size`, `query` e `storeId` opcional.
- O Repository usa páginas de 20 itens.
- O ViewModel mantém busca, loja selecionada e páginas em memória.
- `CatalogPages` une por ID sem duplicar registros; nova primeira página substitui a coleção anterior.
- Uma resposta de busca antiga é descartada quando há uma requisição mais recente.
- Falha ao carregar mais preserva os dados anteriores e permite repetir a página.
- O argumento de navegação é `store_id`; a query HTTP é `storeId`.
- Categoria fica indisponível até existir campo e contrato correspondentes.

O detalhe usa o ID da oferta (`offer_id`) e trata `404`, indisponibilidade e ausência de campos. O Android aceita a proposta de foto opcional `imageUrl` e `items[].imageUrl`, ainda dependente de publicação pela API. Usa apenas HTTPS, placeholder em ausência/falha e nunca inventa URL. Um item único pode fornecer sua foto; múltiplos itens exigem capa explícita. Preço original, promocional e disponibilidade são dados do backend.

A regra esperada do feed é apresentar promoções aprovadas, ativas e vigentes, de lojas ativas e com itens disponíveis. Essa elegibilidade precisa ser garantida e testada **no servidor**; filtro visual no Android não protege o catálogo.

A ordem deve respeitar **mercados mais próximos → maiores descontos percentuais entre as ofertas dessa prioridade**. Por exemplo, 50% tem prioridade sobre 30% na mesma prioridade de distância, independentemente do valor economizado em reais. A precisão/agrupamento de distância e o desempate estável da paginação ainda precisam de definição técnica/produto. Não assumir que um desconto mais alto de uma loja distante deve ultrapassar uma loja mais próxima.

### 10.1 Experiência confirmada de descoberta e rota

1. Após autenticação e com permissão de localização, obter a posição atual do cliente.
2. Identificar os mercados próximos conforme o raio a definir para o produto.
3. Apresentar as promoções elegíveis e disponíveis dessas unidades.
4. Ao tocar numa promoção, abrir o detalhe do produto/oferta com preço, vigência e identificação do mercado responsável, conforme o contrato disponível.
5. Exibir o botão **“Como chegar”** no detalhe.
6. Ao tocar, abrir o **Google Maps oficial**: preferir o aplicativo quando disponível e usar o site como alternativa.
7. Marcar como destino a **unidade vinculada à promoção**, não uma loja diferente da mesma rede, uma pesquisa genérica pelo nome ou a localização do usuário.

O fluxo termina no direcionamento à loja; a compra acontece no próprio mercado. Abrir oferta, tocar em “Como chegar” ou entrar na região da loja não comprova compra nem autoriza conceder pontos ou calcular impacto de uma compra.

Usar coordenadas válidas do mercado; na ausência delas, usar o endereço completo quando puder identificar o destino. Se não houver dados suficientes, informar indisponibilidade em vez de inventar um ponto. A preferência de transporte e a abertura direta de uma rota, em vez de apenas mostrar o destino, devem ser alinhadas com o produto.

**Limitação atual:** a consulta de promoções aceita busca e uma loja, mas a interface Android não envia um filtro geográfico ao feed. Buscar lojas próximas não filtra automaticamente a Home e o Catálogo. É necessário alinhar o contrato de consulta geográfica de promoções com o backend, preservando paginação e critérios de elegibilidade; não basta filtrar uma página de resultados globais no aparelho.

## 11. Lojas, localização e mapa

### 11.1 Lista e coordenadas

Endereço e coordenadas vêm da API. Uma loja sem coordenadas continua elegível à consulta geral conforme o contrato; não deve ganhar um pin fictício. A consulta por proximidade precisa tratar explicitamente a impossibilidade de calcular distância sem coordenadas.

Pin, lista e detalhe da promoção usam `MapNavigation`: abre URL Google Maps com pin da unidade, preferindo o pacote oficial e com alternativa web. Prioriza coordenadas válidas; sem elas, exige rua, número, cidade e estado, incluindo bairro/CEP disponíveis. Dados incompletos não geram pesquisa genérica da rede. Não inicia navegação automaticamente nem escolhe transporte. Sete testes JVM validam URL/endereço; app instalado/ausente e retorno à tela ainda precisam de teste Android.

### 11.2 Localização opcional

O usuário escolhe **5/10/15/20 km**, padrão 5. Localização aproximada/precisa e serviço do aparelho ativo são obrigatórios no uso real. Sem eles, a tela central de acesso orienta a recuperação; não libera lista geral substituta.

O código usa `LocationManagerCompat`, cancelamento e timeout de 15 segundos. A busca é cancelada ao sair da tela. Trocar raio reinicia páginas; Home compartilha o contexto de lojas. Distâncias são aproximações em linha reta, não percurso. Não existe remoção do filtro para consultar todas as lojas nessa tela.

O envio de coordenadas ao backend acontece para atender essa consulta. Não habilitar histórico de localização ou rastreamento contínuo por consequência desse filtro.

**Alvo de produto:** o mapa é uma ferramenta de descoberta em torno da localização atual. O fluxo manual atual de “buscar até 5 km” é uma implementação parcial, não o aceite final dessa experiência. O raio do feed/mapa, o gatilho de atualização e a alternativa quando a localização for negada estão nas decisões em aberto. Atualização visual com o app aberto e monitoramento de entrada em regiões são responsabilidades distintas.

### 11.3 Google Maps

`MOTTAINAI_MAPS_API_KEY` alimenta o Manifest/BuildConfig. A chave precisa ter autorização para o SDK, restrição de aplicativo Android e certificados das variantes usadas. Sem chave válida, a interface deve continuar permitindo consultar endereços e informar o problema.

O mapa mantém a atribuição nativa do SDK. Não adicionar atribuição de OpenStreetMap nem cobrir os controles/termos com overlays.

Permissões declaradas: internet, estado de rede, localização aproximada e precisa. Não há solicitação de localização em background nessa entrega.

## 12. Pontos e histórico

**Finalidade confirmada:** os pontos obtidos na compra de produtos serão usados exclusivamente para medir e apresentar o impacto sustentável do cliente. São uma pontuação de impacto, não uma moeda: cashback, descontos, cupons e resgate de recompensas estão fora do MVP. Não haverá gasto de pontos com resgates. A sugestão anterior de adiar pontos por falta de finalidade fica superada por essa definição.

**Produtos em promoção dão mais pontos**, segundo a decisão de produto compartilhada em 20/10/2026, associando essa pontuação à economia obtida. Isso não define automaticamente multiplicador, proporção com o desconto percentual ou valor economizado. A referência de comparação, a fórmula e a validação da compra devem ser aprovadas antes da implementação; não inferir um programa de pontos para compras não promocionais somente dessa comparação.

Como o app é uma vitrine e não realiza vendas, ele não conhece automaticamente as compras efetuadas no mercado. Ainda é necessário definir como vincular e comprovar a compra do cliente, quanto cada produto gera de pontos e como esses pontos entram nas métricas de impacto. A presença de saldo/histórico não significa que essa concessão ou integração de impacto esteja pronta.

- Saldo e lançamentos vêm da API autenticada.
- A API deve resolver o cliente pelo token e conferir titularidade.
- O app não concede pontos, calcula saldo a partir do histórico, inventa níveis ou executa resgate.
- Saldo e histórico têm carregamentos e erros independentes.
- Dados anteriores em memória podem permanecer visíveis durante atualização, sem significar disponibilidade offline.

O histórico atual solicita seis janelas mensais: mês atual e cinco anteriores. Cada consulta vai do primeiro dia às `00:00:00` até um microssegundo antes do próximo mês. Exemplo de fevereiro de 2026:

```text
from=2026-02-01T00:00:00
to=2026-02-28T23:59:59.999999
```

Os limites são inclusivos e evitam arredondamento para o mês seguinte. O contrato usa datas sem offset; **não assumir que sejam UTC ou horário de Brasília sem alinhar com o backend**. Eventos de fronteira e fuso são critérios de teste.

Quando parte dos meses falha, o ViewModel sinaliza histórico incompleto e pode apresentar dados já disponíveis. A UI não deve mostrar um histórico parcial como completo nem substituir campos ausentes por lançamentos fictícios.

## 13. Perfil e avatar

### 13.1 Contrato protegido atual

`CustomerProfileResponse` lê `id`, `birthYear`, `active` e `marketingConsent`. Os campos de exibição `fullName`, `email` e `phone` são `transient` no DTO Android; não são desserializados como contato em texto aberto.

O app usa Firebase somente para autenticação e e-mail de acesso. Não lê nem grava display name. Na ausência de nome autorizado, Perfil mostra “Cliente” com aviso e Home usa saudação neutra. Após edição SQL confirmada, o nome enviado é mantido somente na resposta em memória para refletir a alteração; ele deixa de estar disponível após nova leitura do contrato protegido.

Para completar a exibição persistente, o backend precisa oferecer uma representação autorizada do perfil, respeitando a proteção do banco. Não basta o Android tentar ler tokens/hashes como nome, nem se deve enfraquecer o schema para corrigir a tela. Não criar cache local/Firebase de nomes para contornar essa ausência.

### 13.2 Edição

A edição atual envia nome, novo telefone e consentimento. Deixar telefone vazio no formulário resulta em omissão/null no JSON para preservar o valor armazenado. A correção da API `fix/customer-profile-update` estabelece: omitido/null mantém; texto vazio explícito remove; novo valor substitui. Conferir a versão realmente implantada antes de testar.

O diálogo aguarda confirmação, mantém os dados digitados em falha e bloqueia ações concorrentes. Há confirmação de logout.

Quando o nome não está disponível, o formulário informa que é preciso digitá-lo para atender o PUT atual, que ainda o exige. Cadastro e edição não alteram nomes já existentes no console Firebase; dados antigos não foram excluídos ou migrados por essa mudança Android.

### 13.3 Avatar

Não há persistência real de avatar concluída. Faltam armazenamento aprovado, autorização, limites de arquivo, referência no perfil e política de substituição/exclusão. Não usar Firebase Storage nem confundir URI local com arquivo enviado.

## 14. Impacto ambiental

A tela usa o mesmo saldo real da área de Pontos, com carregamento, erro, atualização e compartilhamento textual somente após consulta bem-sucedida. Demonstração identifica dados fictícios inclusive no compartilhamento.

**Regra mais recente confirmada:** 1 ponto por real no total gasto, identificado por CPF no PDV Mottainai; devolução/cancelamento estornam pontos. Não aplicar multiplicador por produto em promoção. Pontos representam fidelidade/participação e dão prioridade de recebimento das melhores promoções. Não existe retorno financeiro nem resgate no MVP. Compra/crédito/estorno e prioridade ainda dependem da integração externa.

Não converter saldo em massa de alimentos ou CO₂. Nível/progresso só são exibidos quando informados pelo servidor nos campos opcionais propostos `statusName`/`pointsToNextStatus`. Resposta legada sem esses campos mantém o saldo, com aviso de nível não informado. Faixas de participação não equivalem a certificação ambiental; nenhum nível é calculado pelo Android.

## 15. Assistente

No modo real, o assistente usa HTTP com Firebase ID token. O mecanismo de respostas locais só é criado no modo debug de demonstração. A URL própria é configurada por `MOTTAINAI_ASSISTANT_BASE_URL`; ausência de configuração mostra estado claro, não respostas simuladas.

Os contratos observados implementados são `POST /chat` com apenas `message`/`session_id`, `GET /chat/history/{session_id}` e `GET /chat/sessions`. Há nova conversa, consulta das anteriores, histórico e estados de erro. Respostas de outra conversa são rejeitadas; mensagens system/tool não são apresentadas. O ViewModel preserva a conversa na rotação, sem transcrição em disco. Não há reenvio automático de mensagem após falha de rede ambígua.

Isso não autoriza ligar o consumidor ao fluxo de funcionário: falta homologar suporte explícito ao Cliente e isolamento das contas no serviço. Um `401` exclusivo da IA não limpa a sessão SQL; o token só é renovado conforme o limite já aplicado pelo cliente HTTP.

Não enviar papel/empresa/cliente como forma de conceder permissão. Não colocar chave de LLM no Android. O histórico, se persistido pelo serviço IA, permanece acessível somente por sua API autorizada. Não adicionar histórico offline de negócio ao Cliente.

## 16. Notificações e geofencing

Ambos estão pendentes. Menções a FCM em planos antigos são históricas e **não constituem decisão vigente**.

### 16.1 Comportamento confirmado

Quando o cliente passar perto de uma loja elegível, deve poder receber um aviso sobre as ofertas disponíveis **daquela unidade**. O aviso deve respeitar autorização de notificações/localização e não ser repetido continuamente enquanto a pessoa permanece na região. Não avisar sobre uma promoção expirada, esgotada ou de outra loja como se estivesse disponível no local.

O acionamento considera a posição atual do aparelho, não apenas o endereço cadastrado. O raio padrão é 5 km, com opções 5/10/15/20 km; avisos usam o raio escolhido e devem funcionar em segundo plano, somente online. Cada loja parceira pode enviar até três avisos de produtos diferentes por dia. Quota, deduplicação, elegibilidade e prioridade exigem controle no servidor; não são apenas três destinatários.

### 16.2 Implementação ainda a definir

Uma alternativa discutida é detectar a proximidade no Android, consultar ofertas elegíveis pela API e emitir uma **notificação local**, sem FCM. Isso ainda não define automaticamente todos os mecanismos, permissões ou política de execução em background. Monitorar regiões não significa oferecer catálogo offline; não criar persistência de ofertas no Cliente para contornar a ausência de rede.

Sem conexão não há novos avisos. Não emitir notificação de oferta vigente sem validação. Permissões negadas devem ter tratamento claro e não podem ser contornadas.

Para notificações, definir canal de entrega, registro/remoção da instalação, preferências, tratamento da troca de conta e payload mínimo seguro. Uma notificação interna persistida na API não equivale a push entregue ao aparelho.

Para geofencing, definir elegibilidade das lojas, raio, validade das regiões, cooldown, deduplicação, permissões e comportamento em background. O filtro manual de 5 km não implementa geofencing nem estabelece seu raio. Não solicitar novas permissões sem necessidade, transparência e contrato aprovado.

O destino do toque na notificação — lista de ofertas da loja ou detalhe de uma oferta — ainda será escolhido. Em ambos os casos, revalidar o conteúdo ao abrir e tratar oferta indisponível sem redirecionar silenciosamente para outra promoção.

## 17. Contratos HTTP

### 17.1 Convenções

- Base: `MOTTAINAI_API_BASE_URL`.
- Autenticação das consultas do cliente: `Authorization: Bearer <FIREBASE_ID_TOKEN>`.
- JSON para requests/responses aplicáveis; não enviar senha Firebase no perfil SQL.
- Paginação começa em zero; o app solicita `size=20` no catálogo.
- IDs devem ser tratados como opacos na interface, mesmo quando a API usa inteiros.
- As tabelas abaixo registram chamadas do Android, não comprovam disponibilidade em produção.

### 17.2 Rotas utilizadas

| Método | Rota | Parâmetros/corpo | Uso |
| --- | --- | --- | --- |
| GET | `/api/v1/client/auth/profile` | Sem ID de cliente escolhido pela tela | Perfil da identidade autenticada |
| POST | `/api/v1/client/auth/profile` | `CreateFirebaseCustomerProfileRequest` | Criar/concluir perfil |
| PUT | `/api/v1/client/auth/profile` | `UpdateFirebaseCustomerProfileRequest` | Editar perfil próprio |
| GET | `/api/v1/customer-catalog/stores` | `page`, `size`, `query`, `latitude`, `longitude`, `radiusKm` | Lojas |
| GET | `/api/v1/customer-catalog/stores/{id}` | ID | Detalhe de loja |
| GET | `/api/v1/customer-catalog/promotions` | `page`, `size`, `query`, `storeId` | Promoções |
| GET | `/api/v1/customer-catalog/promotions/{id}` | ID | Detalhe da promoção |
| GET | `/api/v1/client/loyalty/balance` | Sem ID arbitrário | Saldo próprio |
| GET | `/api/v1/client/loyalty/transactions` | `from`, `to` | Histórico próprio |

**Ponto crítico de integração:** as rotas de catálogo ficam fora de `/client/**`. A configuração de segurança da versão implantada precisa aceitar o ID token Firebase nessas rotas e restringir a consulta ao catálogo de consumidor. Não usar login de funcionário/JWT legado como contorno. Existir um controller não comprova autorização correta.

A referência `origin/main` da API foi atualizada e inspecionada em 20/10/2026 (`83c08fa`): a cadeia Firebase já inclui `/api/v1/customer-catalog/**`, com GET autenticado e outros métodos negados. Não foi necessário alterar a API nesta entrega. Isso confirma o código da referência, não qual versão está rodando no ambiente da equipe.

### 17.3 Criação de perfil — estrutura

Exemplo de formato com placeholders; não enviar literalmente nem usar CPF/documentos reais em testes compartilhados:

```json
{
  "fullName": "<nome de teste>",
  "cpf": "<11 dígitos de teste autorizados>",
  "phone": "<telefone de teste>",
  "birthDate": "2000-01-15",
  "marketingConsent": false,
  "address": {
    "zipCode": "<8 dígitos>",
    "street": "<logradouro>",
    "number": "<número>",
    "complement": "",
    "neighborhood": "<bairro>",
    "city": "<cidade>",
    "state": "<UF>"
  }
}
```

O token identifica a conta. `uid`, senha, cargo, empresa e nível de acesso não fazem parte desse payload.

Exemplo ilustrativo dos campos consumidos do perfil protegido, sem garantir que o servidor retorne somente esses campos:

```json
{
  "id": 123,
  "birthYear": 2000,
  "active": true,
  "marketingConsent": false
}
```

### 17.4 Modelos principais

| Modelo Android | Campos relevantes |
| --- | --- |
| `CatalogPage<T>` | `content`, `number`, `size`, `totalElements`, `totalPages` |
| `CatalogStore` | `id`, `name`, `address`, `latitude`, `longitude` |
| Endereço da loja | `zipCode`, `street`, `number`, `complement`, `neighborhood`, `city`, `state` |
| `CatalogPromotion` | `id`, `name`, `description`, `promotionType`, `startsAt`, `endsAt`, `store`, `items` |
| Item da promoção | `id`, `productId`, `name`, `originalPrice`, `promotionalPrice`, `quantityAvailable` |
| `LoyaltyAccount` | `id`, `customerId`, `pointsBalance` |
| `LoyaltyTransaction` | `id`, `transactionType`, `points`, `description`, `createdAt` |

O app usa `BigDecimal` nos DTOs de preços. Não inventar foto/desconto/categoria quando o contrato não os fornece. Mudanças de nomes, tipos, nullabilidade ou datas exigem testes de contrato.

## 18. Erros, concorrência e conectividade

| Condição | Comportamento esperado |
| --- | --- |
| Sem rede / timeout | Mensagem clara e tentativa novamente; não simular sucesso |
| `400`/validação | Preservar formulário e permitir correção |
| `401` | Recuperação de token limitada; sem ciclo de redirecionamento |
| `403` | Informar falta de acesso; não repetir autenticação indefinidamente |
| `404` no perfil durante entrada | Encaminhar à conclusão do cadastro |
| `404` em loja/oferta | Conteúdo indisponível; não abrir cadastro |
| `409` | Tratar conflito/duplicidade sem criar identidade adicional |
| `5xx` | Serviço indisponível e recuperação controlada |
| Corpo vazio/incompleto | Não ativar sessão nem inventar valores |

O cliente autenticado configura conexão de 10 s, leitura de 20 s e chamada de 40 s; a obtenção/renovação do token tem esperas próprias. Esses valores não garantem uma duração total exata para toda a experiência de login, que também envolve Firebase e etapas diferentes.

Requisitos transversais:

- Bloquear duplo envio enquanto a ação estiver em andamento.
- Descartar respostas antigas de busca/filtro.
- Conferir identidade antes de aplicar respostas de perfil.
- Apresentar vazio como vazio, não erro nem conjunto fictício.
- Preservar listas anteriores em memória quando apropriado, com aviso de atualização falha.
- Não adicionar fila de escritas offline ao Cliente.

## 19. Segurança e proteção de dados

### Autorização

- Validar assinatura, emissor, audiência e validade do token no backend.
- Vincular a identidade autenticada ao registro SQL; não confiar em ID enviado pela tela.
- Se houver múltiplos projetos Firebase, considerar emissor/projeto junto ao UID.
- Validar titularidade de perfil e pontos em cada operação.
- Bloquear clientes inativos no backend; uma flag local não concede acesso.
- Conta Firebase válida não concede acesso ao Operacional.

Validação criptográfica básica do token não implica checagem de revogação. A política de bloqueio/revogação deve ser explícita no servidor, além da situação da conta SQL.

### Segredos e configuração

- Não versionar senhas, tokens, service accounts, chaves de LLM ou credenciais de bancos.
- Manter `app/google-services.json` ignorado conforme a política do repositório. Esse arquivo contém configuração do cliente, não é uma chave privada de servidor.
- Não registrar `Authorization`, CPF, telefone, endereço ou corpos sensíveis em logs.
- A chave Maps é distribuída no aplicativo; propriedade Gradle evita exposição no Git, mas não a torna um segredo inviolável. Restringir pacote/certificado/APIs no provedor.
- HTTPS em produção; HTTP somente no ambiente debug previsto pelo projeto.
- Não enviar token da API a ViaCEP ou outros terceiros.

### Privacidade e arquivos futuros

Coletar somente os campos necessários e manter consentimento de marketing separado de permissões Android. Definir finalidade, retenção e exclusão de dados com a equipe. Para avatar, validar tipo/tamanho e autorização; não expor upload irrestrito nem guardar segredo do armazenamento no app.

As regras do Firestore não protegem nossa API SQL. Sem uso de Firestore, a autorização de negócio fica no backend e no banco, não em regras Firebase de documento.

## 20. Configuração do ambiente

### 20.1 Android Studio

1. Abrir a raiz correta do projeto e confirmar branch/checkout.
2. Usar o Gradle Wrapper do repositório.
3. Instalar o SDK requerido e configurar um JDK compatível com AGP/CI.
4. Fazer Sync após alterações de propriedades ou `google-services.json`.
5. Gerar e instalar um APK atualizado; alterar a propriedade local não muda um APK já instalado.

### 20.2 Firebase Authentication

1. Usar o projeto autorizado do Cliente (`mottainai-cliente` na configuração histórica).
2. Registrar o pacote exato `com.mottainai.cliente`.
3. Habilitar E-mail/senha e Google em Authentication.
4. Cadastrar as impressões digitais dos certificados usados, incluindo SHA-1/SHA-256 conforme o provedor e a variante.
5. Baixar novamente a configuração após ajustes necessários e salvar como `app/google-services.json`.
6. Conferir a configuração OAuth/Web client ID usada pelo Google Sign-In.
7. Validar uma conta de teste sem perfil SQL e outra com perfil completo.

Não é necessário criar coleção Firestore para o cadastro. O documento de configuração não substitui a configuração do backend.

Referências: [configuração Android](https://firebase.google.com/docs/android/setup) e [login Google](https://firebase.google.com/docs/auth/android/google-signin).

### 20.3 Propriedades privadas de desenvolvimento

No `gradle.properties` pessoal do usuário, configurar:

```properties
MOTTAINAI_API_BASE_URL=http://10.0.2.2:8080/
MOTTAINAI_MAPS_API_KEY=<chave autorizada para o projeto>
```

Não copiar a chave real para esta documentação, README, commit ou comentário de PR. A base é normalizada para terminar em `/` pelo cliente.

| Ambiente | Endereço da API |
| --- | --- |
| Emulador padrão com backend no computador | `http://10.0.2.2:8080/` no desenvolvimento |
| Aparelho físico | Host HTTPS acessível, IP de desenvolvimento autorizado ou túnel/reverse configurado |
| Backend remoto | URL HTTPS do ambiente combinado com a equipe |

`localhost` no aparelho não aponta para o computador. API em outro computador precisa de acesso de rede, interface/porta publicadas e firewall compatível. Não expor os bancos para resolver acesso do Android.

### 20.4 Backend

O responsável precisa fornecer URL e versão compatível, schema oficial provisionado, dados de teste autorizados e configuração de validação do projeto Firebase (`FIREBASE_PROJECT_ID` no backend existente).

Conferir especialmente:

- Perfil por identidade autenticada e repetição segura do cadastro.
- Catálogo aceitando o token Firebase do consumidor, sem ampliar permissões operacionais.
- Correção de preservação do telefone omitido na edição.
- Titularidade de pontos e semântica de datas.
- Compatibilidade de identidade/PII entre API e versão instalada do banco.

Não executar instaladores SQL ou alterar dados reais como parte da configuração Android. Um `/health` verde não comprova funcionamento de perfil, catálogo ou fidelidade.

### 20.5 Maps

Usar a chave autorizada para o projeto e conferir habilitação do Maps SDK, restrições e condições do projeto Google Cloud com o responsável. Chave de outro pacote/certificado pode produzir mapa vazio. Não ampliar restrições indiscriminadamente para fazer funcionar.

Referência: [configurar Maps SDK for Android](https://developers.google.com/maps/documentation/android-sdk/get-api-key).

## 21. Testes e critérios de aceite

### 21.1 Automatizados existentes

| Teste | Responsabilidade |
| --- | --- |
| `ProfileSyncStatusTest` | Distinguir acesso, conclusão de perfil e erro |
| `CatalogPagesTest` | União ordenada, deduplicação e sequência de páginas |
| `LoyaltyPeriodTest` | Limites mensais e fevereiro bissexto |
| `CustomerProfileResponseTest` | Contrato protegido e campos transitórios |
| `DemoDataTest` | Consistência de dados demonstrativos |

O histórico de entrega registra 14 testes JVM aprovados e CI debug aprovado na entrega de 18/10/2026. Isso é evidência daquela revisão, **não uma nova execução nem status atual de todas as PRs**. Consultar `delivery-status.md` e a execução correspondente.

Em 20/10/2026, na continuação local `fix/firebase-auth-only`, foram compilados com JDK 19 (`--release 11`) e executados diretamente via JUnit os cinco arquivos de teste listados acima: **17 testes passaram**. Isso inclui os novos casos de perfil inativo/sem situação, respostas `202`/`204` e exclusão de campos de apresentação do JSON. Não foi executado Gradle, APK ou teste com Firebase/API reais nessa verificação.

Também passou a compilação direta do núcleo atual de autenticação: Repository, ViewModel, validação de perfil, DTOs e dependências-fonte de rede/sessão, usando bibliotecas já disponíveis em cache. A tentativa mais ampla com Activities não concluiu porque as classes/R geradas disponíveis eram antigas e havia dependências incompletas nesse classpath manual; os IDs citados existem nos XMLs atuais. Isso não é aprovação de compilação das telas. Foram conferidos estaticamente 58 XMLs de recursos, o Manifest, referências removidas de display name e links/índice deste documento. O build Gradle e o teste visual permanecem com a responsável no Android Studio.

O workflow do checkout executa:

```text
./gradlew testDebugUnitTest lintDebug assembleDebug --no-daemon --stacktrace
```

No PowerShell, usar `.\gradlew.bat` com as mesmas tarefas. Esses comandos são um roteiro para a responsável executar; não foram rodados para produzir este documento.

### 21.2 Roteiro manual

| Área | Cenários mínimos |
| --- | --- |
| Entrada | Senha correta/incorreta, Google, cancelamento e cliques repetidos |
| Cadastro | Duas etapas, voltar, rotação, CEP inválido, endereço manual e consentimento |
| Perfil pendente | Firebase criado + API indisponível; recuperar sem duplicar conta |
| Sessão | Fechar/abrir, logout, trocar conta com requisição em andamento, `401` persistente |
| Home | Falhar uma seção sem bloquear as demais; tentar novamente |
| Catálogo | Busca rápida, vazio, duas páginas, filtro de loja, detalhe e retorno |
| Feed geográfico, após implementação | Mercados dentro/fora do raio, mudança de posição e paginação sem misturar regiões |
| Rota da promoção, após implementação | Abrir a unidade anunciada no Google Maps oficial; testar alternativa web e endereço/coordenadas ausentes |
| Paginação | Falhar a próxima página e repetir sem duplicar anteriores |
| Mapa | Coordenadas ausentes, chave ausente/inválida e atribuição visível |
| Localização | Aproximada/precisa, recusa, GPS desligado, timeout e revogação |
| Pontos | Saldo zero real, vazio, mês bissexto, fronteira de datas e erro parcial |
| Perfil | Salvar nome/consentimento sem apagar telefone; preservar formulário em falha |
| Perfil ativo | Testar `active=false`, `active` ausente, ID inválido e HTTP `202`/`204`; não liberar sessão |
| Firebase somente Auth | Cadastrar/editar sem alterar display name Firebase; conferir apresentação neutra após recarregar perfil |
| Sem internet | Mostrar indisponibilidade, sem prometer consultas offline |
| Avisos por proximidade, após implementação | Entrada/permanência/reentrada, permissões negadas, falta de rede, oferta expirada e limite de frequência |
| Demonstração | Somente debug, sem gravar no backend ou aparentar dados reais |
| Acessibilidade/UI | Fontes ampliadas, contraste, rotação, teclado e toque em componentes |

### 21.3 Testes de backend necessários

- Token inválido, expirado ou de projeto não autorizado.
- Tentativa de acessar perfil/pontos de outro cliente.
- Criação repetida do perfil sem duplicidade e conflito de documento.
- Acesso Firebase ao catálogo e separação de permissões cliente/funcionário.
- Exclusão de promoções não aprovadas, expiradas e de lojas inativas.
- Paginação, busca e filtro geográfico, incluindo coordenadas ausentes.
- Atualização parcial preservando telefone e dados protegidos.

## 22. Pendências e sequência de implementação

| Ordem | Entrega | Critério de conclusão |
| --- | --- | --- |
| 1 | Alinhar versão API/banco e catálogo Firebase | Cliente real autentica, consulta perfil e catálogo sem credencial operacional |
| 2 | Completar leitura do perfil de negócio | Dependência Firebase removida localmente; falta fonte oficial autorizada no backend |
| 3 | Integrar feed por proximidade e destino Google Maps | Home/Catálogo limitados ao contexto geográfico; detalhe abre a unidade correta no app/site oficial |
| 3.1 | Homologar conta, Home, lojas e pontos | Roteiro integrado executado com dados de teste |
| 4 | Avatar | Upload autorizado, armazenamento aprovado e referência persistida |
| 5 | Impacto baseado em pontos de compras | Comprovação da compra, concessão de pontos e regra de conversão aprovadas, com consulta real |
| 6 | Assistente consumidor | Autorização própria e isolamento de dados/sessões comprovado |
| 7 | Notificações de ofertas por proximidade | Conteúdo, destino e limites aprovados, sem depender de Firebase além de Auth |
| 8 | Geofencing | Detectar proximidade da unidade, confirmar ofertas e evitar repetição; regras/permissões e teste em aparelho |
| 9 | Preparação de release | HTTPS, assinatura, privacidade, revisão de dependências e aceite |

### Responsabilidades

| Responsável | Precisa fornecer/decidir |
| --- | --- |
| Equipe Android | Implementação, estados, navegação, contratos cliente e testes automatizados |
| Equipe API/banco | Contratos, autorização, transações, schema oficial, dados protegidos e ambiente |
| Produto | Métricas de impacto, regras de notificações/geofencing e campos realmente necessários |
| Responsável Firebase/Google | Provedores, certificados, acesso ao projeto e restrições Maps |
| Infraestrutura | URLs, HTTPS, armazenamento de arquivos, observabilidade e políticas de retenção |
| Isabella/equipe de QA | Compilação no Android Studio e aceite em emulador/aparelho |

Sem URL/versão compatível e dados oficiais de teste, não declarar homologação concluída. Sem definição de impacto, arquivo ou push, não inventar provedor/endpoint somente para fechar uma tela.

## 23. Branches, commits e PRs

- Usar `feat/` para funcionalidade e `fix/` para correção. Não usar `codex/`.
- Manter PRs pequenas, com poucos commits e responsabilidade clara.
- Convenção: `<type>(<scope>): <subject>`, subject em sentence-case, até 100 caracteres.
- **Pedir confirmação antes de push ou abertura de PR.** O push aciona o bot e também depende dessa autorização. Após confirmação, deixar o bot abrir a PR, conforme o fluxo da equipe.
- Não mergear automaticamente. Conferir base e dependências de PRs encadeadas.
- Não marcar checklist de build, teste ou UI que não foi executado.
- Manter frontend draft separado de promessa de backend concluído.

Exemplo de commit:

```text
feat(profile): Load customer display data from the authorized API
```

Descrição deve conter `O que muda`, `Por que`, `Como testar`, checklist, issues e screenshots quando houver UI. Dependência de contrato/backend deve estar explícita. O histórico das entregas e branches de 18/10 está em [delivery-status.md](cliente/delivery-status.md); o estado remoto precisa ser conferido antes de novas ações.

## 24. Diagnóstico de problemas

| Sintoma | Verificar primeiro |
| --- | --- |
| Login Firebase funciona, mas aparece falha ao sincronizar | URL, rede/porta e versão da API; não recriar a conta |
| Google não abre/recusa configuração | Provedor habilitado, pacote, assinatura SHA e configuração OAuth |
| Perfil funciona, catálogo retorna `401/403` | Segurança do prefixo `customer-catalog` para token Firebase |
| Alterar consentimento apaga telefone | Versão implantada da correção de atualização parcial |
| Nome não aparece após recarregar o perfil | O GET protegido não retorna nome; apresentação neutra é intencional até contrato autorizado |
| Mapa vazio | Chave Maps, SDK, restrições de pacote/certificado e conectividade |
| Sem localização, mas lista funciona | Não é o comportamento aprovado; conferir o bloqueio central e a variante debug/demonstração |
| Lista vazia | Diferenciar ausência real de promoções elegíveis, filtro ativo e erro HTTP |
| Pontos não batem com compras | Conferir lançamentos/regras no servidor; não corrigir saldo no Android |
| Tela existe, mas dados são indisponíveis | Conferir se é funcionalidade pendente ou demonstração |
| Gradle não inicia | Conferir JDK usado pelo wrapper e Android Studio; não alterar autenticação por isso |

Coletar status HTTP, horário, versão e identificador de requisição quando disponível. Remover tokens e dados pessoais antes de compartilhar logs.

## 25. Referências e manutenção

### Documentos do repositório

- [README](../../README.md): apresentação e entrada do projeto.
- [Autenticação e retomada](cliente/authentication.md): comportamento e roteiro da implementação anterior.
- [Catálogo e lojas](cliente/catalog.md): paginação, mapa e aceite.
- [Contratos pendentes](cliente/remaining-contracts.md): diagnóstico histórico de integrações.
- [Estado das entregas](cliente/delivery-status.md): branches e verificações registradas em 18/10.

Este documento prevalece sobre textos anteriores **nas decisões de Firebase somente para autenticação e ausência de offline no Cliente**. Os documentos históricos continuam úteis para entender a implementação, mas menções antigas a FCM ou display name não representam aprovação da arquitetura final.

### Fontes oficiais consultadas

- [Configuração Firebase Android](https://firebase.google.com/docs/android/setup).
- [Autenticação Google no Android](https://firebase.google.com/docs/auth/android/google-signin).
- [Verificação de ID tokens no servidor](https://firebase.google.com/docs/auth/admin/verify-id-tokens).
- [Configuração Maps SDK](https://developers.google.com/maps/documentation/android-sdk/get-api-key).

### Base desta documentação

Conferência no checkout `Mottainai-Mobile-Cliente-work`, branch local `fix/firebase-auth-only`, derivada de `fix/client-ci`. A documentação inicial foi registrada no commit local `27699f1`. O índice estrutural anterior estava desatualizado e suas ferramentas não estavam disponíveis na continuação; os contratos e comportamentos materiais foram conferidos nos arquivos atuais. Documentos de entrega citam referências históricas da API e IA; não representam auditoria da versão implantada.

Esta continuação modifica somente o Android Cliente e a documentação. Não altera a pasta original em StudioProjects, API, bancos ou infraestrutura. Não foram executados build Gradle Android, migração SQL, configuração de console ou teste ponta a ponta nesta etapa. Resultados dos testes locais são registrados separadamente após execução; não substituem a compilação e o aceite no Android Studio.

Ao alterar um endpoint, fonte de dados, permissão ou serviço, atualizar a seção correspondente e registrar se a mudança está apenas planejada, implementada, publicada ou homologada. Nunca converter uma proposta em comportamento atual somente por editar o texto.

## 26. Alinhamento de produto e decisões em aberto

### 26.1 Fluxo confirmado em 20/10/2026

**Localização atual → mercados próximos → promoções disponíveis → detalhe da promoção → botão “Como chegar” → Google Maps oficial com a unidade anunciada como destino.**

Antes desse fluxo, exigir conta e autenticação: não há modo visitante para serviços de produção. As ofertas priorizam mercados mais próximos e depois maiores descontos percentuais; a relação desconto/vencimento já faz parte da regra comercial informada. O app é uma vitrine, e a compra acontece exclusivamente no mercado. Os pontos obtidos nessas compras serão usados para medir o impacto do cliente, com comprovação e cálculo ainda a definir.

Em paralelo: **passagem próxima à loja → verificação das ofertas → notificação de proximidade**, respeitando as permissões e as regras ainda a fechar.

O escopo está confirmado, mas a integração geográfica do feed, a garantia de destino Google Maps e os avisos automáticos ainda não foram concluídos. O filtro manual de lojas de 5 km e o intent genérico existentes não equivalem a esse fluxo completo.

### 26.2 Perguntas para fechar as regras

As alternativas abaixo são perguntas, não decisões aprovadas nem valores padrão a implementar sem alinhamento.

| ID | Tema | Pergunta em aberto |
| --- | --- | --- |
| A01 | Região do feed | Qual o raio inicial para mercados e ofertas: manter 5 km ou outro? O cliente pode alterá-lo? |
| A02 | Ordenação — prioridade confirmada | Proximidade primeiro e desconto percentual decrescente depois; maiores descontos já refletem vencimento próximo. Faltam precisão da distância e desempate estável. |
| A03 | Sem localização ou sem ofertas | Permitir escolher mercado/cidade/endereço manualmente? Se não houver oferta próxima, manter vazio ou oferecer ampliação explícita do raio? |
| A04 | Movimento no mapa | Atualizar a região automaticamente ao mudar de posição, ao reabrir a tela ou somente quando o cliente pedir? |
| A05 | Raio do aviso | A qual distância da loja avisar: por exemplo, 200 m, 500 m ou 1 km? É diferente do raio do feed? |
| A06 | Background | Os avisos precisam funcionar com o app fora da tela e após reiniciar o aparelho, mediante permissões? Como explicar a ativação ao cliente? |
| A07 | Frequência e preferências | Quantos avisos por loja/dia? Há horário silencioso, categorias favoritas ou desativação por loja? |
| A08 | Toque no aviso e rede | O aviso abre ofertas da loja ou uma promoção específica? Sem rede para confirmar disponibilidade, não avisar ou usar mensagem genérica sem afirmar que há oferta vigente? |
| A09 | Google Maps | Abrir somente o destino marcado ou iniciar o fluxo de rota? Deixar o cliente escolher transporte ou definir uma preferência? |
| A10 | Compra — vitrine confirmada | Compra exclusivamente no mercado, não pelo aplicativo. Falta definir a atualização da disponibilidade; reserva não foi solicitada nem está autorizada como nova funcionalidade. |
| A11 | Pontos e impacto — finalidade confirmada | Pontos de compras servem somente ao impacto sustentável; produtos em promoção dão mais pontos. Sem cashback, descontos, cupons ou resgate no MVP. Faltam comprovação/vínculo da compra, referência e fórmula da pontuação adicional, métricas/conversão oficial, período e tratamento de cancelamentos. |
| A12 | Acesso confirmado / cadastro em aberto | Conta/login obrigatórios para todos os serviços; sem visitante. Falta decidir quais dados pessoais são obrigatórios e em qual etapa devem ser pedidos. |
| A13 | Demais módulos | Qual a finalidade do assistente, de onde vêm suas respostas e quais funções pessoais são prioridade depois do núcleo de ofertas? |

Registrar as respostas nesta seção antes de transformar opções em regras fixas. Questões de raio/frequência não devem ser inferidas de valores de demonstração. Decisões técnicas de armazenamento de fotos e retorno autorizado de perfil continuam pendentes nas seções próprias.
