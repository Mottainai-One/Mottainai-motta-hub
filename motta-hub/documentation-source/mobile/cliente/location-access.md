# Acesso por sessão e localização

> Código local de 21/10/2026, sem push/PR. Não representa build APK ou homologação de permissões no aparelho.

## Fluxo implementado

1. Firebase autentica e a API confirma perfil SQL ativo, como no contrato anterior.
2. Antes de criar as telas principais, `ClientAccessGuard` exige sessão válida, permissão de localização aproximada ou precisa e localização do aparelho ativada.
3. Sem sessão, encaminha ao login. Sem localização, encaminha à `LocationAccessActivity`, sem inflar Home/Catálogo/Pontos/Perfil da área principal.
4. A tela explica o requisito, permite solicitar permissão por ação explícita, abrir configurações do app, ativar localização do aparelho, verificar novamente ou sair da conta. Não solicita permissão automaticamente em loop.
5. Conceder/ativar permite retornar à área principal; encerrar sessão retorna ao login. O botão Voltar pode encerrar essa tela, mas não libera serviços.
6. Main, detalhe da oferta e assistente revalidam o requisito ao retornar ao primeiro plano. Ao bloquear, limpam a pilha de navegação: o detalhe anterior não é retomado automaticamente.

Isso é um bloqueio de interface, não substitui validação Firebase, titularidade e autorização no servidor. A exceção de demonstração continua restrita a `BuildConfig.DEBUG` pelo `SessionManager`.

## Posição e raio

- Home e Lojas usam a mesma instância de `CatalogViewModel` da Activity para lojas. A posição é solicitada ao entrar/retornar à Main e também por atualização manual; o raio escolhido em Lojas vale para os dois mapas, sem consulta global substituta.
- Raio 5/10/15/20 km, padrão 5. Mudança reinicia páginas e invalida resposta anterior.
- Permissão não é posição obtida: `ForegroundLocationRepository` faz uma leitura, com timeout de 15 segundos, valida coordenadas e revalida acesso antes de aceitar a resposta. Home mostra obtenção da posição separadamente de carregamento da API e permite tentar de novo sem abrir Lojas.
- Main cancela leitura pendente ao sair do primeiro plano; o ViewModel também cancela ao ser descartado. Trocar abas não cancela o pedido compartilhado nem cria GPS concorrente. Respostas canceladas/antigas não atualizam a busca. Não há GPS contínuo nem geofencing neste fluxo.
- Coordenadas permanecem somente em memória. Raio usa ViewModel/Bundle como estado de tela, não perfil local oficial. Process death exige nova leitura de posição.
- Home e Catálogo ainda consultam o contrato de promoções anterior, sem ordenação geográfica completa. Não confundir mapa de lojas integrado com feed de ofertas geográficas pronto.

## Ainda não entregue

Preferência oficial no cadastro/SQL, contrato de promoções geográficas e ordenação antes de paginar, geofencing/background, quota de avisos e prioridade por fidelidade, integração PDV/pontos/estornos, avatar, imagens e autorização consumidor da IA. A nova tela não promete notificações já funcionando.

## Verificação

- 47 testes JVM aprovados: a base anterior de 36 mais 5 de coordenadas e 6 de CPF. São testes da lógica Java, não testes de Activities/SDK Firebase ou da obtenção real do GPS.
- 59 XMLs e Manifest analisados; conferir correspondência das novas strings/IDs e registro não exportado da Activity.
- Não executados Gradle, APK, lint ou teste UI nesta etapa, conforme responsabilidade de Android Studio combinada.

Roteiro de Isabella: login sem permissão; negar uma vez e permanentemente; autorizar aproximada/precisa; desligar GPS; voltar das configurações; revogar permissão no detalhe/assistente; girar a tela; sair da conta no bloqueio; encerrar/reabrir processo; conferir debug demo e inexistência de modo visitante release. Verificar que cadastro/recuperação continuam acessíveis e que não ocorre ciclo de telas.

Também testar: leitura automática na Home; troca para Lojas durante leitura; sair do app antes da resposta e voltar; mudança de raio durante leitura; timeout; novo ponto não reaproveitar páginas antigas. Núcleo de localização/ViewModel compilado diretamente contra Android/AndroidX em cache; isso não substitui APK/lint/UI.

Referência técnica: [permissão de localização no Android](https://developer.android.com/develop/sensors-and-location/location/permissions/runtime).
