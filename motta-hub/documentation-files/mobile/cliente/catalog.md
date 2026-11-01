# Catálogo e lojas

O ViewModel mantém as páginas já carregadas, a busca e o filtro de loja durante a recriação da tela. As telas substituem a lista pelo snapshot observado, sem reaplicar páginas a cada observação.

- `GET /api/v1/customer-catalog/promotions`: `page`, `size`, `query` e `storeId`.
- `GET /api/v1/customer-catalog/stores`: `page`, `size`, `query`, `latitude`, `longitude` e raio selecionado em `radiusKm` (5/10/15/20), usando o contrato existente. A tela não faz consulta geral sem posição.
- IDs de loja trafegam pela navegação no argumento `store_id`; “Ver ofertas de todas as lojas” remove o filtro, mantendo a busca.
- Repetição da mesma página não duplica registros. Falha no carregamento seguinte preserva os dados anteriores e permite repetir a página que falhou.
- Pin, lista e detalhe da promoção usam o mesmo auxiliar de Google Maps. “Como chegar” abre pin pelas coordenadas válidas ou endereço completo da unidade (rua, número, cidade e estado), preferindo app oficial e usando URL web como alternativa; ausência de destino ou aplicativo compatível exibe aviso.
- O mapa é Google Maps; a atribuição é fornecida pelo próprio SDK. Os textos de estado ficam fora da área inferior de atribuição.

## Roteiro de aceitação

Imagens: DTOs aceitam os campos opcionais propostos `imageUrl` e `items[].imageUrl`; a API ainda precisa publicá-los/aprová-los. Cards e detalhe usam Glide com HTTPS sem credenciais, placeholder em ausência/falha e sem cache offline. Só um produto único pode fornecer sua imagem implicitamente; vários produtos exigem referência explícita de capa. Não é uma integração direta Android → Open Food Facts/Cosmos.

1. Carregar duas páginas e girar a tela; conferir ordem e ausência de duplicação ou recarga da primeira página.
2. Abrir uma oferta, voltar e conferir busca/páginas anteriores.
3. Selecionar uma loja pela lista e pelo pin; conferir o mesmo endereço, a rota e ofertas com `storeId`.
4. Buscar e carregar mais dentro de uma loja; o filtro deve continuar aplicado. Remover o filtro pela ação explícita.
5. Interromper a rede na segunda página, recuperar e repetir; a primeira continua visível e a segunda não é anexada duas vezes.
6. Alternar buscas rapidamente, inclusive limpar o campo; uma resposta antiga não deve substituir a consulta atual.
7. Conferir lojas sem coordenadas, endereço incompleto, mapa sem chave, unidades da mesma rede e caracteres especiais. Testar Google Maps instalado/desativado/ausente e ausência de navegador; conferir o destino no detalhe da promoção e nas ações da loja. Não deve iniciar navegação automaticamente.
8. Escolher 5/10/15/20 km e buscar localização: conferir permissão precisa/aproximada, GPS desligado, timeout e recusa. Sem posição, mapa/lista ficam indisponíveis, sem consulta global substituta. A tentativa novamente deve orientar a autorização/obtenção da posição.
9. Conferir o mesmo raio nas páginas seguintes. Trocar o raio reinicia na página zero, descarta resposta pendente antiga e não mistura regiões. Recriar a tela mantém o raio; processo recriado precisa de nova posição. Distâncias em linha reta.
10. Main inicia leitura ao entrar/retornar ao primeiro plano e cancela pedido pendente ao sair do app; trocar Home/Lojas acompanha o mesmo pedido. Revogar permissão ou desligar GPS e voltar bloqueia serviços. Nenhuma permissão de background é solicitada nesta etapa.
11. Conferir foto publicada, ausência, URL inválida, erro HTTP e rolagem rápida: nenhuma foto reciclada de outra oferta pode permanecer. Uma imagem indisponível não deve bloquear preço/detalhe.

`CatalogPagesTest` cobre união ordenada, repetição de página, troca de filtro, páginas fora de sequência, IDs ausentes e retenção dos dados em loading/erro.

`GoogleMapsUrlTest`: sete testes JVM aprovados em 21/10 para destino por coordenadas/endereço completo, unidades distintas, caracteres especiais, dados incompletos e coordenadas zero. `MapNavigation` e dependências compilados diretamente contra `android-31/android.jar`; isso não equivale a build APK ou teste de abertura de aplicativo no aparelho.

`OfferRadiusTest` valida padrão, quatro opções permitidas e rejeição de valores não aprovados. Raio é estado de tela (ViewModel/Bundle), sem persistir coordenadas nem criar perfil local/Firestore. Home e Lojas compartilham contexto de lojas; [bloqueio central](location-access.md) exige sessão e localização no uso real. Ainda faltam preferência oficial no endereço e feed de promoções geográfico/ordenado no backend. Não considerar esse recorte como geofencing/notificações implementados.
