# Mottainai Mobile Operacional — documentação funcional e técnica

> Atualização: **19/10/2026**. Este documento descreve o propósito, os perfis, os fluxos e o estado observado no código local do aplicativo. **Tela implementada não significa operação persistida na API, publicada na main ou homologada ponta a ponta.**

## Índice

1. [Objetivo e público](#1-objetivo-e-público)
2. [Decisões e limites](#2-decisões-e-limites)
3. [Perfis e permissões](#3-perfis-e-permissões)
4. [Estado das funcionalidades](#4-estado-das-funcionalidades)
5. [Navegação e experiência](#5-navegação-e-experiência)
6. [Arquitetura e estrutura](#6-arquitetura-e-estrutura)
7. [Autenticação e sessão](#7-autenticação-e-sessão)
8. [Home](#8-home)
9. [Produtos e cadastro](#9-produtos-e-cadastro)
10. [Scanner](#10-scanner)
11. [Inventário físico](#11-inventário-físico)
12. [Fornecedores](#12-fornecedores)
13. [Avarias e perdas](#13-avarias-e-perdas)
14. [Inteligência — alertas](#14-inteligência--alertas)
15. [Inteligência — sugestões](#15-inteligência--sugestões)
16. [Inteligência — chat](#16-inteligência--chat)
17. [Perfil e foto](#17-perfil-e-foto)
18. [Configurações e equipe](#18-configurações-e-equipe)
19. [Notificações](#19-notificações)
20. [Persistência e offline](#20-persistência-e-offline)
21. [APIs e contratos](#21-apis-e-contratos)
22. [Configuração do ambiente](#22-configuração-do-ambiente)
23. [Segurança e tratamento de erros](#23-segurança-e-tratamento-de-erros)
24. [Testes e critérios de aceite](#24-testes-e-critérios-de-aceite)
25. [Pendências e sequência de entrega](#25-pendências-e-sequência-de-entrega)
26. [Referências e manutenção](#26-referências-e-manutenção)

## 1. Objetivo e público

O Operacional é o aplicativo Android usado pelos funcionários e responsáveis pelas lojas do ecossistema Mottainai. Seu propósito é apoiar o controle dos produtos, a conferência do estoque físico e a identificação de oportunidades de reduzir perdas e desperdício.

O app reúne consulta de produtos, leitura de códigos de barras, contagem de inventário, fornecedores, avarias, alertas e apoio de inteligência artificial. Cada perfil deve visualizar as informações e ações necessárias ao seu trabalho, respeitando empresa, loja e autorização.

Não é o aplicativo do consumidor. Descoberta de ofertas, pontos do cliente e consulta pública de lojas pertencem ao Mobile Cliente. Uma promoção aprovada no Operacional só deve chegar ao Cliente depois de gravada e publicada pelos serviços oficiais; navegar para uma tela de sucesso não publica uma oferta.

## 2. Decisões e limites

- Interface Android em **Java e XML**, com a identidade visual Mottainai.
- Login do mobile por **e-mail e senha no Firebase Authentication**. Não substituir pelo login CPF/senha do site.
- A orientação do projeto é manter dados de negócio nas APIs; empresa e loja devem ser resolvidas pelo backend relacional. O código ainda possui dependências legadas de Firestore, descritas neste documento.
- O papel é utilizado na experiência mobile; a API precisa validar identidade, vínculo e permissão independentemente da interface. Claims de papel não substituem autorização por empresa/loja no servidor.
- O Android não se conecta diretamente ao PostgreSQL, MongoDB ou Redis e não recebe suas senhas.
- Offline é uma necessidade do Operacional, mas a preparação atual não implementa sincronização universal de escritas.
- Mocks e exemplos são ferramentas de desenvolvimento, não fonte oficial nem comprovação de integração.
- Cloudinary foi considerado para fotos; a escolha não significa upload integrado ou contrato concluído.
- A existência atual de FCM, Firebase Storage e Firestore não deve ser tratada como aprovação automática de todos esses serviços na arquitetura final.

## 3. Perfis e permissões

### 3.1 Responsabilidade de cada perfil

**Estoquista:** execução da rotina física da loja: localizar produtos, consultar informações, usar scanner, conferir quantidades e identificar avarias. Tem acesso a alertas e ao chat operacional, mas não à aba de sugestões nem às configurações do Dono.

**Gerente:** acompanhamento da operação e manutenção de produtos e fornecedores, além da consulta de sugestões e de sua tela de decisão. Deve revisar divergências e oportunidades de redução de perdas. A gravação real dessas decisões ainda é uma pendência.

**Dono:** visão de gestão, acesso às funções disponíveis ao Gerente e entrada exclusiva nas configurações. A área inclui regras, preferências de notificações e equipe, sem significar que automações, convites ou alterações de cargo já estejam operacionais no backend.

### 3.2 Matriz de acesso observado na interface

Legenda: **Sim** = fluxo acessível no Android; **Não** = restrição explícita no fluxo normal; **Parcial** = interface disponível, mas operação remota incompleta. Não é certificação da segurança dos endpoints.

| Funcionalidade | Estoquista | Gerente | Dono | Ressalva |
| --- | --- | --- | --- | --- |
| Login e perfil próprio | Sim | Sim | Sim | Identidade e sessão completas |
| Home | Sim | Sim | Sim | Conteúdo varia pelo papel |
| Lista, busca e detalhe de produtos | Sim | Sim | Sim | Origem mock ou HTTP conforme checkout/configuração |
| Scanner e consulta por código | Sim | Sim | Sim | Consulta não equivale a entrada/saída de estoque |
| Cadastrar/editar produto | Não | Sim | Sim | `canRegisterProduct`; API deve validar permissão |
| Contagem física de inventário | Sim | Sim | Sim | Fluxo local, não ajusta estoque SQL |
| Consultar fornecedores | Sim | Sim | Sim | Fonte local por loja |
| Criar/editar/remover fornecedor | Não | Sim | Sim | Manutenção local, sem CRUD remoto integrado |
| Abrir registro de avaria | Parcial | Parcial | Parcial | Formulário acessível pelo scanner, sem gravação real nesse caminho |
| Consultar alertas | Sim | Sim | Sim | Repositório atual usa Firestore |
| Consultar sugestões | Não | Sim | Sim | Ocultas para Estoquista |
| Ajustar desconto e ver prévia | Não | Parcial | Parcial | Simulação visual, sem publicação |
| Aprovar/recusar sugestão | Não | Parcial | Parcial | Botões ainda informam dependência de integração |
| Chat com IA | Sim | Sim | Sim | Backend limita dados e ações por identidade |
| Abrir configurações | Não | Não | Sim | `isOwner`, validado também ao abrir a tela |
| Preferências de regras/notificações | Não | Não | Parcial | Salvas neste dispositivo |
| Gerenciar equipe | Não | Não | Parcial | Exemplo e formulários; sem convite/edição remotos |
| Alterar foto de perfil | Pendente | Pendente | Pendente | Perfil atual usa iniciais |
| Sair da conta | Sim | Sim | Sim | Confirmação e limpeza local |

### 3.3 Limites das permissões atuais

`RoleHelper.normalize` aceita papéis em português e aliases legados: `ADMIN`/`OWNER` → Dono, `MANAGER` → Gerente e `STOCK` → Estoquista. Esse mapeamento é compatibilidade de interface, não criação de privilégio no servidor.

O helper de sugestões bloqueia explicitamente Estoquista, mas não funciona como allowlist estrita: papel nulo ou desconhecido não é recusado por esse helper isoladamente. A matriz acima considera os três papéis válidos com sessão completa. É necessário endurecer esse comportamento e conferir proteção das rotas de detalhe/decisão, inclusive por navegação direta.

Não afirmar que esconder botão protege uma operação. O servidor precisa recusar acesso indevido mesmo quando a chamada é feita fora do APK.

## 4. Estado das funcionalidades

| Área | Estado observado | O que falta para considerar concluída |
| --- | --- | --- |
| Autenticação | Firebase integrado ao fluxo Android | Conferir contas, claims, perfil e vínculo SQL no ambiente atual |
| Navegação e abas | Implementadas | Homologar teclado, retorno e recriação das telas |
| Produtos | Modo mock e repositório HTTP | Contrato completo e teste com API/banco compatíveis |
| Scanner | Implementado | Teste por aparelho e integração com dados oficiais |
| Inventário | Contagem local | Sessão remota, reconciliação e ajuste autorizado |
| Fornecedores | CRUD local | Endereço e demais campos exigidos pela API |
| Avarias | Demonstração/integração parcial | Gravação efetiva, baixa transacional e fotos |
| Alertas e sugestões | Leitura via Firestore | Migrar para fonte oficial e validar escopo |
| Decisão de sugestão | Interface e cálculo de prévia | Persistir decisão e publicar promoção |
| Chat IA | Cliente HTTP com Firebase direto | Dados locais, vínculos e serviços prontos para novo teste integrado |
| Perfil | Consulta e logout | Perfil oficial e foto persistida |
| Configurações | Preferências locais | Contratos e execução de regras no servidor |
| Equipe | Telas parciais | Listagem, convite e manutenção autorizados |
| Notificações | Recepção FCM e tratamento Android | Registro remoto do dispositivo e cadeia de entrega |
| Offline | Preparação local em branch de integração | Homologação e sincronização de escritas por contrato |

## 5. Navegação e experiência

A navegação principal reúne Home, Produtos, scanner central elevado, Inteligência e Perfil. Configurações são abertas a partir do Perfil pelo Dono.

- **Produtos:** abas Lista, Inventário e Fornecedores dentro da mesma seção, usando ViewPager2; a troca não deve abrir três seções independentes.
- **Inteligência:** Alertas, Sugestões e Chat. O Estoquista mantém Alertas e Chat, sem Sugestões.
- **Configurações:** Regras, Notificações e Equipe.
- Scanner abre detalhes do produto, cadastro permitido ou registro de avaria conforme o resultado e papel.
- Campo de busca deve aceitar toque em toda a área editável, não apenas na lupa.
- Teclado não deve cobrir quantidade física, observação ou mensagem do chat; o botão central não deve sobrepor campos e ações.

As cores dos protótipos enviados são referências de composição, não substituição da paleta Mottainai. Seleção de abas, foco, contraste e estados desabilitados devem seguir os componentes do projeto.

## 6. Arquitetura e estrutura

```text
Activity / Fragment + XML
          |
          v
ViewModel + LiveData
          |
          v
Repository
  |              |                    |
Firebase Auth    Retrofit / OkHttp     Mocks / persistência local
                 |
                 v
           APIs autorizadas
                 |
                 v
       Bancos e serviços internos
```

O código atual também consulta Firestore em repositórios legados. Essa dependência deve ser identificada ao migrar cada fluxo; o desenho acima representa a separação pretendida, não uma migração finalizada.

| Camada | Responsabilidade |
| --- | --- |
| Activity/Fragment e adapters | Interação, navegação e apresentação |
| ViewModel | Estado, carregamento, validações de fluxo e resultados |
| Repository | Escolha da fonte e tradução de respostas/erros |
| DTOs e serviços Retrofit | Contrato HTTP, sem credenciais de infraestrutura |
| Sessão e armazenamento local | Contexto e cópias limitadas; nunca autorização oficial |
| Backend | Identidade, autorização, regras, transações e auditoria |

Identificação do checkout: pacote `com.mottainai.operacional`, minSdk 26, compile/target SDK 36 e fontes Java 11. A versão Java das fontes não determina sozinha o JDK necessário para executar Gradle.

Estrutura principal:

```text
app/src/main/
  java/com/mottainai/operacional/
    MainActivity.java
    activities/
    fragments/
    adapters/
    models/
    network/
    repository/
    viewmodels/
    utils/
    notifications/
    storage/             preparação offline local
  res/layout/
  res/navigation/
  res/values/
app/src/test/
app/src/androidTest/
docs/
scripts/                 configuração/diagnóstico locais
```

## 7. Autenticação e sessão

### 7.1 Fluxo existente

1. O funcionário informa e-mail e senha.
2. O app autentica pelo Firebase.
3. `UserRepository` consulta `users/{uid}` no Firestore, lendo nome, papel e `storeID`.
4. O login renova o ID token e exige claims `storeID` e `role`.
5. O app mantém a sessão local e abre a área principal.
6. No checkout de integração, a entrada principal confere identidade Firebase, UID da sessão e perfil completo antes de montar a navegação.

Cadastrar somente uma conta no Firebase não garante perfil operacional completo. Registrar um UID em arquivo local também não cria documento Firestore, custom claims ou vínculo SQL. Esses são estados diferentes.

### 7.2 Integração com APIs

O token é enviado como `Authorization: Bearer <Firebase ID Token>`. A senha Firebase não é enviada ao login CPF da API SQL nem ao serviço IA.

O chat atual envia o token Firebase diretamente à IA. O backend verifica a identidade e resolve funcionário, empresa, loja e papel no banco. O contrato da revisão local da IA ainda exige UID vinculado e e-mail canônico protegido; revisões mais recentes do banco alteram esse contrato para UID. É necessário compatibilizar versões antes de atualizar o schema.

Claims e perfil usados na navegação não garantem que a API aceite o token ou encontre a conta. Validar assinatura, emissor, audiência, expiração, situação da conta e autorização no servidor.

### 7.3 Logout e conectividade

O Perfil confirma a saída, limpa estado local pertinente e remove a pilha de navegação. A limpeza de token de notificações local não comprova desvinculação no servidor.

Primeiro login e operações de autenticação exigem conectividade. Sessão já existente pode permitir reabertura offline na preparação local, sem garantir acesso a toda informação ou permissão online ainda vigente.

## 8. Home

A Home apresenta saudação, contexto do papel, alertas e atalhos. Gerente possui cards de gestão e sugestões; Dono possui uma composição de visão geral/financeira; Estoquista tem foco em alertas de estoque.

Parte dos contadores é derivada das listas já carregadas. Campos financeiros ainda sem fonte são apresentados com `—`. Há também valor fixo de lojas ativas no código conferido; não documentar esse número como indicador real multi-loja.

Conclusão esperada: indicadores oficiais com unidade, período, origem e autorização; estados independentes de carregamento, vazio e erro. Um card existente não comprova cálculo financeiro implementado.

## 9. Produtos e cadastro

Lista, busca e detalhe permitem consultar o catálogo operacional. Gerente e Dono podem abrir cadastro e edição; Estoquista tem consulta.

O checkout local de integração permite escolher mocks por `useMockProducts`. Em debug, o padrão é mock; em release, o seletor de produtos é real. Isso **não desliga os mocks de inventário ou avarias**, que continuam separados.

O repositório HTTP possui listagem paginada, detalhe, busca por código, criação e atualização. Antes de concluir a integração, conferir composição de produto com preço, estoque e lote: SKU não é sinônimo de código de barras, e fornecedor não é marca.

Validação local ajuda o usuário; duplicidade, campos obrigatórios, vínculo com loja e autorização precisam ser garantidos pela API. Não inserir produto fictício após uma falha HTTP.

## 10. Scanner

O scanner utiliza câmera, leitura de código, lanterna quando disponível e feedback sonoro/tátil. Há tratamento de ciclo de vida da câmera e opção de entrada manual no fluxo existente.

Fluxo principal: ler/informar código → consultar fonte configurada → mostrar produto encontrado → abrir detalhe ou registrar avaria. Produto não encontrado pode encaminhar Gerente/Dono ao cadastro com o código preenchido; Estoquista não deve ganhar permissão de cadastro por esse atalho.

Leitura de código não altera quantidade nem registra movimentação automaticamente. Consultas externas de identificação de produto também não constituem cadastro oficial nem podem receber o token da API Mottainai.

Sem rede, a preparação offline só permite localizar produtos já disponíveis nas cópias locais; não transforma a câmera em acesso ao catálogo completo.

## 11. Inventário físico

### 11.1 Propósito e fluxo

Conferir estoque esperado contra quantidade física observada:

1. Iniciar contagem para a loja da sessão.
2. Carregar itens demonstrativos no fluxo atual.
3. Informar quantidade física e, quando necessário, observação.
4. Acompanhar itens conferidos e resumo de faltas/excessos.
5. Conferir todos os itens e justificar divergências.
6. Confirmar finalização; edição é bloqueada na sessão local.

Antes de iniciar, a tela informa que a contagem ainda não começou, em vez de tratar `0 de 0` como progresso útil. Ao abrir o teclado, o cabeçalho é ocultado e a lista ajusta o espaço para revelar o campo em edição.

### 11.2 Regras existentes e limites

O ViewModel impede finalizar com itens não conferidos ou divergências sem observação. A tela explica que a finalização é demonstrativa: **não altera estoque SQL e não envia alerta automático ao Gerente**.

A branch local de integração adiciona persistência de rascunhos por usuário/loja. Isso ainda não é sincronização com o servidor. Existem textos antigos na UI que mencionam memória apenas; precisam ser alinhados à implementação antes da entrega.

Para concluir: contrato de sessão/itens, responsável e timestamps, base esperada, revisão gerencial, ajuste transacional, trilha de auditoria, concorrência e envio idempotente. Cadastro simples de estoque e histórico de movimentações não substituem esse contrato de contagem física.

## 12. Fornecedores

Estoquista consulta; Gerente e Dono criam, editam e removem no fluxo local. O repositório mantém dados por loja em SharedPreferences e inclui exemplos demonstrativos.

Nome da empresa e CNPJ de 14 dígitos são exigidos localmente; contar dígitos não comprova validade cadastral. O contato é opcional nesse modo.

O contrato relacional documentado exige campos adicionais, como endereço, nome comercial, e-mail e telefone. A tela ainda não resolve todo esse cadastro remoto. Portanto, salvar um fornecedor aqui não comprova que ele foi criado na API ou compartilhado com outro dispositivo.

## 13. Avarias e perdas

O fluxo pretende registrar produto, motivo e quantidade afetada, apoiando rastreabilidade da perda. A tela acessível pelo scanner valida motivo e quantidade positiva.

**Limite concreto:** `RegisterDamageFragment` navega diretamente para a tela de sucesso depois da validação, sem chamar o repositório. Separadamente, `DamageRepository` possui implementação mock e contrato HTTP declarativo. A existência desse repositório não significa que o formulário o utilize.

É necessário ligar o formulário à gravação real, aguardar confirmação, validar disponibilidade e motivo no servidor, definir impacto em estoque e impedir duplicidade. Fotos, notas e eventual upload devem ser testados no caminho efetivamente utilizado, não apenas em uma classe isolada.

Não interpretar essa tela de sucesso como baixa de estoque, movimentação oficial ou perda financeira persistida.

## 14. Inteligência — alertas

Alertas apoiam a priorização de itens que precisam de atenção. O código diferencia severidades `CRITICO`, `ATENCAO` e `MONITOR`.

`AlertRepository` ainda escuta Firestore, filtrando `storeID` e janela de dias. Declarar uma rota de alertas em Retrofit não migra automaticamente esse repositório para a API.

A origem final precisa definir regra, data de cálculo, empresa/loja, produto/lote e ação disponível. Ausência de alerta, falha da consulta e dados antigos são estados distintos.

## 15. Inteligência — sugestões

### 15.1 Experiência pretendida

O card reúne produto, tipo da ação, justificativa da IA e ações Aprovar/Recusar. Gerente e Dono acessam a seção.

- Aprovar abre o detalhe, com desconto proposto e possibilidade de ajuste.
- O app mostra **o preço do produto após o desconto**, sem transformar esse preço em campo de edição.
- Recusar no card abre uma confirmação sobre possível manutenção do risco de perda; não afirmar perda futura como certeza.

### 15.2 Cálculo e origem dos dados

```text
preço sugerido = preço atual × (1 − desconto / 100)
```

Exemplo ilustrativo: preço R$ 12,90, desconto de 20%, prévia R$ 10,32. O preço atual deve vir da fonte oficial; o desconto inicial vem da IA. Alterar a porcentagem atualiza a prévia, não o preço-base do produto.

Na tela atual há valores de fallback demonstrativos quando os argumentos não trazem preço/desconto. Não apresentar esses valores como consulta oficial. Validar intervalo de desconto, arredondamento monetário e políticas no servidor antes de publicar.

### 15.3 Estado real

As sugestões ainda são lidas do Firestore. O detalhe calcula a prévia e permite digitação de desconto, mas seus botões de decisão apenas informam integração pendente. A confirmação de recusa do card também não persiste a decisão.

Para concluir: carregar produto/preço oficiais, validar elegibilidade e autorização, gravar aprovação/recusa, registrar justificativa e responsável, prevenir decisões duplicadas e publicar a promoção no catálogo apropriado. A IA recomenda; o Android não pode afirmar publicação sem confirmação do backend.

## 16. Inteligência — chat

O chat fica dentro da aba Chat de Inteligência, não em um botão que leva a uma área independente. Possui mensagens do usuário/assistente e campo de pergunta, respeitando teclado e botão central do scanner.

O cliente usa a API IA com token Firebase direto. O serviço deve vincular sessão e histórico ao usuário, restringir dados por empresa/loja/papel e recusar leitura de conversas de outra identidade. A disponibilidade da aba para todos os perfis não concede a todos acesso financeiro de Dono.

Histórico local e histórico no servidor são fontes distintas. Na preparação offline, mensagens previamente salvas podem ser lidas; novas perguntas exigem conexão. Falha de IA não deve produzir uma resposta fictícia apresentada como real.

Há registro histórico de smoke test Firebase/IA dos três papéis em ambiente isolado em 14/10. Esse registro tem escopo de login/chat e fixtures daquela execução; não comprova que o novo ambiente local de 19/10 já esteja vinculado ou que as demais funções estejam integradas.

## 17. Perfil e foto

Perfil apresenta nome, e-mail, iniciais, papel e loja/contexto da sessão. O logout exige confirmação. Para Dono, aparece a entrada de Configurações.

A versão conferida usa iniciais como avatar; não possui alteração de foto persistida concluída. Para Cloudinary ou outro armazenamento aprovado, faltam política de upload, tamanho/formato, assinatura quando aplicável, referência no perfil e tratamento de substituição/exclusão. Chave secreta de upload deve permanecer no servidor.

Nome comercial da loja e empresa devem vir da API relacional, não ser presumidos a partir do identificador local. Dados exibidos no perfil não concedem permissão.

## 18. Configurações e equipe

Somente Dono acessa a seção no fluxo normal; a própria tela verifica o papel.

| Aba | Propósito | Implementação observada |
| --- | --- | --- |
| Regras | Parametrizar promoção/doação e aprovação | Preferências locais; a tela não configura automações efetivas no servidor |
| Notificações | Escolher categorias de avisos | Switches locais utilizados pelo tratamento Android |
| Equipe | Consultar membros e administrar acessos | Membro de exemplo e formulários parciais |

O salvamento de regras atual persiste os booleanos de promoção automática e exigência de aprovação. Não documentar todos os números/controles mostrados no protótipo como parâmetros remotamente gravados.

Convite valida e-mail, mas informa endpoint pendente. Salvar/remover membro também apenas informa pendência. Não cria conta Firebase, altera claims nem desativa funcionário SQL.

Para concluir equipe: listagem real, vínculo autorizado com empresa/loja, convite com aceite, edição/desativação auditada e sincronização de autorização. Um seletor de papel no Android nunca deve permitir autoelevação de privilégio.

## 19. Notificações

O código contém captura/renovação de token FCM, canais Android, permissão no Android 13+, deduplicação e roteamento de destinos conforme papel. Há limpeza local no logout.

O contrato histórico de dispositivos é uma proposta documentada, não endpoint confirmado como integrado. Não há comprovação de envio do token à API nem de entrega remota nesta preparação.

Redis API e push são camadas diferentes: armazenar uma notificação ou marcá-la como lida não faz o aparelho recebê-la. Também é necessário compatibilizar a autenticação da API Redis com a identidade mobile.

A decisão de usar Firebase apenas para autenticação precisa ser conciliada explicitamente com o FCM existente antes da entrega. Não presumir que o desenho de push está aprovado apenas porque a dependência consta no Gradle.

## 20. Persistência e offline

### 20.1 Origem atual e destino pretendido

| Informação | Fonte atual observada | Direção/limite |
| --- | --- | --- |
| Identidade e senha | Firebase Authentication | Manter autenticação no Firebase |
| Perfil inicial e papel/loja da navegação | Firestore e claims/sessão | Alinhar com cadastro e autorização oficiais |
| Produtos | Mock ou API SQL | API como fonte de negócio |
| Estoque/lotes/movimentações | Integração incompleta no app | API relacional, sem conexão direta ao banco |
| Contagem física | Repositório local | Sessões e reconciliação no servidor pendentes |
| Fornecedores | SharedPreferences por loja | CRUD remoto pendente |
| Alertas e sugestões | Firestore | Migrar para contratos oficiais |
| Conversas IA | API IA; cópia local na preparação | Mongo acessado pelos serviços, não pelo Android |
| Regras e preferências | Armazenamento local | Regras de negócio precisam de backend |
| Foto | Iniciais/sem persistência concluída | Serviço de objetos e contrato a definir |

### 20.2 Preparação offline da branch local

- Catálogo real mantém cópias de respostas recebidas; produtos não baixados continuam indisponíveis.
- Índice de produtos é limitado aos últimos 500; histórico local de chat, a 200 mensagens.
- Erros HTTP de autorização não devem ser contornados usando cache.
- Cópias são segregadas por contexto de usuário, loja, papel e servidor.
- Rascunhos de inventário persistem no espaço privado da conta/loja, sem envio automático ao SQL.
- Logout limpa caches de catálogo/chat; rascunhos permanecem restritos à conta original nessa preparação.
- Banner de desconexão sinaliza possível desatualização.
- Limpar dados ou desinstalar remove dados locais; armazenamento privado não é backup de negócio.

Essas mudanças estão no checkout de integração com alterações locais. Não afirmar que chegaram à main ou ao APK instalado sem conferir a versão usada.

### 20.3 O que ainda não existe como entrega completa

Não há fila universal de criação de produto, avaria, decisão ou movimentação offline. Cada escrita precisa de idempotência, confirmação e tratamento de conflito antes de ser sincronizada. Mostrar sucesso offline não substitui essas garantias.

## 21. APIs e contratos

### 21.1 Responsabilidades dos serviços

| Componente | Responsabilidade |
| --- | --- |
| API SQL | Cadastros e operações relacionais autorizadas |
| IA | Chat, histórico, agentes e consultas permitidas |
| Redis API | Notificações/fluxos definidos pelo serviço; integração mobile pendente |
| Mongo API | Consulta/curadoria interna dos dados IA; não expor diretamente ao app |
| PostgreSQL operacional | Dados oficiais e vínculos operacionais |
| PostgreSQL analítico | Publicações analíticas usadas por consultas IA |
| MongoDB | Conversas, memória, RAG, execuções e métricas conforme serviço |
| Redis | Cache, limites, eventos e idempotência conforme contrato |

### 21.2 Chamadas declaradas no Android

| Método | Rota | Situação |
| --- | --- | --- |
| GET | `/api/v1/products` | Cliente de produtos, com paginação/busca |
| GET | `/api/v1/products/{id}` | Detalhe |
| GET | `/api/v1/products/barcode/{barcode}` | Consulta por código |
| POST | `/api/v1/products` | Cadastro, sujeito à configuração e autorização |
| PUT | `/api/v1/products/{id}` | Atualização |
| GET | `/api/v1/alerts` | Declarada; repositório ativo conferido usa Firestore |
| GET | `/api/v1/suggestions` | Declarada; repositório ativo conferido usa Firestore |
| POST | `/api/v1/damages` | Declarada; fluxo de formulário ainda não integrado |
| POST | `/chat` | Chat na base da IA |
| GET | `/chat/history/{sessionId}` | Histórico na base da IA |

Uma anotação Retrofit não comprova que o endpoint exista na versão implantada, aceite Firebase ou esteja sendo chamado pela tela. Contratos de fornecedores, inventário e notificações precisam de conferência nas versões oficiais antes de novos consumidores.

## 22. Configuração do ambiente

### 22.1 Android

1. Abrir o checkout/branch correto no Android Studio.
2. Conferir pacote `com.mottainai.operacional` e configuração do projeto Firebase autorizado.
3. Configurar endpoints em `local.properties` ignorado pelo Git.
4. Fazer Sync, gerar e instalar um APK novo.
5. Conferir contas, perfil/claims atuais e vínculo SQL; apenas registrar e-mail/UID num arquivo não provisiona nada.

Exemplo para emulador, com APIs no mesmo computador nas portas abaixo:

```properties
apiBaseUrl=http://10.0.2.2:8080/
iaBaseUrl=http://10.0.2.2:8000/
useMockProducts=true
```

`useMockProducts` pertence à preparação local conferida; validar se a branch usada possui esse parâmetro. Para testar catálogo HTTP nessa branch, alterar para `false` após preparar a API. Isso não migra os demais fluxos.

`10.0.2.2` é o host visto pelo emulador padrão. Aparelho físico precisa de IP acessível ou `adb reverse`; APIs em outro computador precisam de rede/VPN, porta publicada e firewall compatíveis. As portas de QA podem ser diferentes, como 18080/18000; usar o mapeamento do ambiente escolhido, não misturar receitas.

HTTP fica restrito a debug; release precisa de endpoints HTTPS aprovados. Endereço compilado no APK não muda quando se edita apenas um arquivo local depois da instalação.

### 22.2 Situação local em 19/10

PostgreSQL, MongoDB e Redis da instalação isolada foram verificados saudáveis. Python da IA terminou a instalação e as 24 coleções oficiais do Mongo passaram na verificação. Isso não significa que as quatro APIs HTTP estejam iniciadas nem que exista empresa/loja/funcionário provisionado.

O novo ambiente ainda precisa de vínculos operacionais, dados autorizados de teste e carga/publicação analítica para consultas correspondentes. A configuração dos três usuários foi registrada localmente sem senhas; ainda não equivale a vínculo SQL ou alteração no Firebase.

Não reinstalar schema nem apagar volumes para iniciar um teste. Guardar `.env`, tokens e credenciais fora do Git; usar o roteiro local específico da IA para subir serviços com a configuração correta.

## 23. Segurança e tratamento de erros

- Validar usuário, empresa, loja e papel no backend em cada operação protegida.
- Não confiar em papel/empresa enviados livremente pelo app ou em IDs manipulados.
- Não colocar chaves LLM, Firebase Admin, Cloudinary secret ou conexões dos bancos no APK.
- Não registrar senha, Authorization, tokens ou dados pessoais desnecessários em logs.
- Distinguir falta de rede, token inválido, falta de permissão, conflito e ausência real de dados.
- Preservar formulário em erro; bloquear envio concorrente; não repetir escrita de resultado desconhecido sem idempotência.
- Não converter falha de rede em logout automático nem sucesso fictício.
- Revogação de permissões e isolamento entre contas precisam ser testados; cache não concede autorização.

| Condição | Tratamento esperado |
| --- | --- |
| Sem rede/timeout | Aviso e tentativa novamente; cópia local somente onde suportada |
| 400 | Corrigir campos, preservando dados digitados |
| 401 | Recuperação de autenticação controlada; sem loop |
| 403 | Informar acesso negado; não promover papel local |
| 404 | Produto/recurso indisponível ou vínculo ausente, conforme contrato |
| 409 | Conflito/duplicidade, com reconciliação |
| 5xx | Serviço indisponível; sem confirmar gravação |

Esses são critérios transversais de entrega, não afirmação de que todas as telas já implementam cada tratamento.

## 24. Testes e critérios de aceite

### 24.1 Por perfil

- **Estoquista:** consultar produtos, escanear, contar e justificar divergência; conferir ausência de cadastro de produto, manutenção de fornecedor, sugestões e configurações.
- **Gerente:** testar manutenção permitida, acesso a sugestões e ausência de configurações exclusivas do Dono.
- **Dono:** testar visão correspondente, configurações e limites explícitos das funções ainda locais.
- **Todos:** verificar login, troca de conta, logout, teclado, retorno entre abas, listas vazias, erro e reabertura.
- Testar papel desconhecido e tentativa de abrir destino restrito diretamente; o comportamento deve negar acesso.

### 24.2 Por integração

1. Conta Firebase autentica e o servidor resolve o vínculo correto.
2. Consulta retorna dados somente da empresa/loja autorizada.
3. Cadastro/edição continua existente após atualizar em outro cliente autorizado.
4. Inventário remoto só muda estoque depois de confirmação e validação do servidor.
5. Avaria não mostra sucesso antes de persistir e não duplica por toque/repetição.
6. Sugestão usa preço real, recalcula desconto e publica somente após resposta autorizada.
7. Chat não permite histórico de outra conta nem dados financeiros fora do papel.
8. Notificação usa evento real, não duplica e respeita preferências/destino.
9. Offline preserva apenas dados previstos e não anuncia sincronização que não aconteceu.

### 24.3 Verificações técnicas

Executar na branch da entrega, com ambiente compatível:

```powershell
.\gradlew.bat assembleDebug
.\gradlew.bat lint
.\gradlew.bat test
```

Os documentos locais registram testes anteriores de chat e de armazenamento offline com escopos próprios. Não foram executados novo build, lint, teste em aparelho ou teste integrado para produzir esta documentação. CI verde de compilação não substitui autenticação e operações reais.

## 25. Pendências e sequência de entrega

| Ordem | Entrega | Critério de conclusão |
| --- | --- | --- |
| 1 | Fixar versões e ambiente | API/banco/IA compatíveis, serviços acessíveis e dados de teste autorizados |
| 2 | Identidade operacional | Firebase válido + funcionário/empresa/loja + papel, sem depender de vínculo fictício |
| 3 | Produtos e scanner reais | Leitura/escrita homologadas e composição de preço/estoque correta |
| 4 | Fornecedores | Cadastro completo e CRUD remoto autorizado |
| 5 | Inventário | Sessão, divergência, revisão e ajuste transacional com auditoria |
| 6 | Avarias | Formulário ligado ao serviço, baixa/registro reais e duplicidade controlada |
| 7 | Alertas e sugestões | Fonte oficial, preço real, decisão persistida e publicação |
| 8 | Perfil/configurações/equipe | Cadastro oficial, regras efetivas e administração segura |
| 9 | Fotos | Upload autorizado e referência persistida |
| 10 | Notificações | Transporte aprovado, dispositivo registrado e entrega validada |
| 11 | Offline de produção | Escritas idempotentes, conflitos e isolamento homologados |
| 12 | Release | HTTPS, privacidade, build/lint/testes e aceite por perfil |

Essa sequência organiza dependências, não renumera automaticamente as antigas etapas MOBILE. Cada entrega deve ser analisada e testada antes do próximo merge, como combinado com a equipe.

Branches devem seguir `feat/` ou `fix/`, sem `codex/`. Commits no formato `<type>(<scope>): <subject>`. PRs precisam registrar mudanças, motivo, como testar e limitações; não marcar verificações que não ocorreram. Push/PR/merge não foram feitos nesta entrega documental.

## 26. Referências e manutenção

### Base conferida

Checkout **`Mottainai-Mobile-Operacional-integration`**, branch **`feat/operational-api-offline`**, commit-base **`0e2e0f9`**, com alterações locais não commitadas. O documento não é uma auditoria da main remota ou do APK instalado.

O serviço Codebase Memory estava indisponível (`Transport closed`); a verificação foi feita diretamente nos arquivos. Não foi possível validar geração/cobertura do grafo. As constatações são limitadas aos fluxos e fontes citados; documentos históricos não foram tratados como prova de disponibilidade atual no servidor.

Arquivos centrais conferidos, relativos ao checkout:

- `app/build.gradle.kts`, `MainActivity.java` e `res/navigation/nav_graph.xml`.
- `utils/RoleHelper.java` e `utils/Constants.java`.
- `fragments/HomeFragment.java`, `ProductsListFragment.java`, `ScannerFragment.java` e `InventoryFragment.java`.
- `viewmodels/InventoryViewModel.java`.
- `fragments/IaAlertsFragment.java` e `ApproveSuggestionFragment.java`.
- `fragments/RegisterDamageFragment.java` e `repository/DamageRepository.java`.
- `fragments/ProfileFragment.java`, `ConfigFragment.java`, `InviteMemberFragment.java` e `EditMemberFragment.java`.
- `repository/UserRepository.java`, `AlertRepository.java` e `SuggestionRepository.java`.
- `network/ApiService.java` e declarações de `AiApiService.java`.

Os caminhos Java acima pertencem a `app/src/main/java/com/mottainai/operacional/`; o XML de navegação pertence a `app/src/main/`.

Documentos complementares no checkout:

- [Autenticação Firebase da IA](Mottainai-Mobile-Operacional-integration/docs/AI_FIREBASE_AUTH.md).
- [Ambiente e preparação offline](Mottainai-Mobile-Operacional-integration/docs/API-SETUP-AND-OFFLINE.md).
- [Contrato histórico de notificações](Mottainai-Mobile-Operacional-integration/docs/MOBILE-09-NOTIFICATIONS-CONTRACT.md).
- [Perfil](Mottainai-Mobile-Operacional-integration/docs/MOBILE-10-PROFILE.md).
- [Fornecedores](Mottainai-Mobile-Operacional-integration/docs/MOBILE-10-SUPPLIERS.md).

Documentos de ambiente anteriores contêm checkpoints datados; a situação local mais recente registrada aqui não os torna atualizados automaticamente. Este arquivo descreve decisões e implementação, sem criar permissão ou contrato no servidor por meio do texto.

Ao alterar origem de dados, papel, endpoint, persistência ou estado de entrega, atualizar a seção correspondente e indicar se está **planejado, implementado localmente, publicado ou homologado**. Não incluir credenciais nem dados pessoais reais em exemplos.
