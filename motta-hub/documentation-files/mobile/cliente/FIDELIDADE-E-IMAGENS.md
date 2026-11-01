# Cliente — fidelidade, avisos e pesquisa de imagens

> Definições e pesquisa de 21/10/2026. Documento local; não publica código, contratos ou serviços. Regras confirmadas e propostas estão separadas. Complementa o [guia](../MOBILE-CLIENTE.md) e o [plano](PLANO-IMPLEMENTACAO.md).

## 1. Regras confirmadas pelo produto

- Raios: **5, 10, 15 e 20 km**, com padrão 5 km, escolhidos na confirmação do endereço. O raio dos avisos acompanha o das ofertas.
- Localização obrigatória para serviços; apenas lojas parceiras Mottainai. Avisos precisam funcionar em segundo plano, com autorização Android. Sem internet, não emitir aviso.
- Cada loja pode enviar **até três avisos por dia, de produtos diferentes**. A quota de seleção/emissão pertence à loja/dia, não é uma autorização para escolher três novos produtos para cada cliente. Distribuir um aviso aos destinatários elegíveis não equivale a consumir toda a quota com os primeiros três destinatários. Confirmar no contrato o fuso do dia e evitar reenvio do mesmo aviso à mesma conta.
- Clientes com mais pontos recebem primeiro as melhores promoções; os demais recebem depois. Não confundir essa ordem de comunicação com reserva/exclusividade ou mudança da ordenação distância/desconto no catálogo.
- **Um ponto por real sobre o total gasto na compra**, comprovada pelo PDV e vinculada pelo **CPF**; base total confirmada posteriormente pelo produto. Cancelamento/devolução retira o crédito correspondente. O tratamento dos centavos não foi explicitado, portanto não inferir arredondamento nem fracionamento.
- Essa fórmula substitui a hipótese anterior de bônus automático para produtos em promoção. Não aplicar multiplicador promocional sem nova decisão.
- Avatar somente Cloudinary. Imagem da oferta é a mesma do produto, obtida de API externa.

## 2. Proposta inicial de status

| Pontuação válida | Nome |
| --- | --- |
| 0 a menos de 100 | Semente |
| 100 a menos de 500 | Broto |
| 500 a menos de 1.500 | Planta |
| 1.500 a menos de 3.000 | Árvore |
| 3.000 ou mais | Floresta |

Faixas criadas para o Mottainai, não extraídas de uma norma ambiental ou comprovadas como ideais por pesquisa. Sugestão para o MVP: pontos acumulados confirmados menos estornos, sem expiração automática; níveis recalculados no servidor, inclusive após devolução. Período/expiração ainda não foram aprovados pelo produto. A prioridade considera os pontos reais, não somente o nome da faixa; empate não pode ser decidido pelo CPF.

Justificativa: primeiro marco acessível e intervalos posteriores progressivos, com indicação clara de quanto falta para o próximo nível. A pesquisa de Kivetz, Urminsky e Zheng encontrou intensificação de participação perto de metas em programas de recompensa; não valida estes valores nem demonstra benefício ambiental. Não usar progresso fictício, incentivo a comprar além da necessidade ou promessa de estoque para estimular gasto.

O nome de tela recomendado é **“Sua jornada Mottainai”**, com explicação: “Nível de participação baseado em compras confirmadas. Não representa certificação ambiental nem cálculo de CO₂ evitado.” Pode compor a área de Impacto, mas dinheiro gasto não comprova alimento efetivamente salvo. A metodologia do UNEP mede desperdício com dados próprios de medição; não autoriza equivalência de reais/pontos para massa ou emissões.

Depois do piloto, avaliar distribuição de clientes e tempo até os marcos, com dados agregados, antes de alterar faixas. Não rotular quem gasta menos como menos sustentável.

## 3. Cálculo e integração: cuidados do contrato

- Usar o valor total efetivamente pago e confirmado pelo PDV, conforme produto, não apenas o desconto/economia ou uma seleção promocional dos itens.
- Centavos ainda exigem decisão: `R$ 12,90` pode gerar `12,90` pontos proporcionais ou pontos inteiros com regra definida. Recomendação: manter proporcionalidade decimal, sem perda por fracionar compras. Não implementar arredondamento por conta própria.
- Processar dinheiro com decimal exato ou centavos inteiros, nunca ponto flutuante binário. Backend calcula; Android não concede pontos.
- Associar compra a cliente existente pelo CPF no serviço autorizado, sem expor busca pública de CPF. CPF é identificador de vínculo, não senha nem prova de autorização. Normalizar/validar e usar a proteção oficial do banco; não criar armazenamento em texto aberto por conveniência.
- Evento do PDV autenticado, venda única e estados confirmada/cancelada/devolvida; replay não duplica crédito. Estorno total e parcial precisam refletir o crédito original e preservar histórico. Cadastro inexistente e vinculação tardia exigem comportamento explícito, não cadastro automático.
- Comunicação prioritária ainda precisa de **janela de antecedência e tamanho/critério do primeiro grupo**. Apenas ordenar uma lista de destinatários não garante que os maiores pontuadores recebam antes; definir liberação por etapas no servidor. Notificações locais só podem emitir conteúdo cuja fase esteja liberada para a conta.
- Background é requisito confirmado, não promessa de entrega instantânea: geofencing, permissões específicas, restrições de bateria, limite de regiões e retomada precisam ser testados em aparelho. Force-stop e falta de rede não podem ser contornados com garantia fictícia.

## 4. API de imagens: recomendação pesquisada

### Open Food Facts — primeira opção para piloto do MVP

API de alimentos com consulta por código de barras e URLs de fotos de produto. Recomendação técnica: consultar pelo GTIN/EAN exato no backend, selecionar imagem frontal correspondente e publicar referência/fonte no catálogo. Não substituir preço, estoque ou validade do mercado por dados desse provedor. Card e detalhe usam a mesma referência.

Limitações: base colaborativa, sem garantia de foto ou correspondência para todo produto; itens frescos/sem GTIN e não alimentícios podem ficar sem imagem. Usar placeholder, não buscar uma foto parecida pelo nome. A documentação estabelece limites por endpoint e identificação por User-Agent. Confirmar versão suportada na implementação; não fixar neste plano um endpoint marcado como legado.

Licenças: base sob ODbL e imagens sob CC BY-SA. Registrar atribuição e condições aplicáveis; revisar o desenho de reutilização antes de misturar dados em um catálogo proprietário. Não supor que API pública significa uso irrestrito nem que separar tabelas elimina obrigações. Cache de referência no servidor somente conforme termos/política aprovados; isso não cria modo offline no Android.

### Cosmos / Bluesoft — alternativa a avaliar

Catálogo orientado ao varejo brasileiro com consulta de produto por GTIN. API exige token e User-Agent; limites dependem das políticas de acesso. O provedor informa licenças por item, que precisam ser conferidas. Antes de escolhê-lo, validar credencial/plano, campo de imagem na resposta e autorização de exibição/reutilização. Não há benchmark com os produtos Mottainai nem prova de que sua cobertura de fotos seja superior.

Não integrar dois fornecedores e uma camada genérica de fallback agora: testar primeiro um. Não contratar plano nem criar conta automaticamente.

### Aceite antes da integração

1. Receber amostra de 20–50 GTINs reais de parceiros, sem dados pessoais.
2. Medir presença e correspondência da imagem (marca, variante, peso/volume), além de disponibilidade e tempo de resposta; amostra ainda não executada.
3. Validar atribuição/licença, limites e exposição somente da referência necessária.
4. Tratar produto inexistente, sem foto, indisponibilidade/429 e mudança de referência sem bloquear o feed.

**Escolha recomendada:** Open Food Facts para piloto, sem ativação em produção até validar cobertura e termos. Cosmos permanece alternativa, não dependência adicional automática.

## 5. Fontes primárias consultadas

- [Kivetz, Urminsky e Zheng, 2006 — estudo de metas em programas de recompensa](https://journals.sagepub.com/doi/pdf/10.1509/jmkr.43.1.39).
- [UNEP — Food Waste Index Report 2024, metodologia e medição](https://www.unep.org/resources/publication/food-waste-index-report-2024).
- [Open Food Facts — API, limites e licenças](https://openfoodfacts.github.io/openfoodfacts-server/api/).
- [Open Food Facts — consulta de produto e imagens, referência v2 legada](https://openfoodfacts.github.io/documentation/docs/Product-Opener/v2/products/get-product-by-code/).
- [Cosmos — API, autenticação e consulta GTIN](https://api.cosmos.bluesoft.com.br/api).
- [Cosmos — licenças dos dados por item](https://api.cosmos.bluesoft.com.br/licenses).
- [Android — geofencing, permissões e limitações de background](https://developer.android.com/develop/sensors-and-location/location/geofencing).

Essas fontes sustentam as capacidades/limitações descritas; não aprovam as faixas numéricas, a política comercial Mottainai nem dispensam a revisão dos termos de uso.
