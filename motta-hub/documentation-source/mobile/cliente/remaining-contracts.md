# Dependências para concluir o Mobile Cliente

> Atualizado em 21/10/2026. Esta frente altera somente Android. O contrato detalhado para a outra equipe está em [DEMANDAS-API-CLIENTE.md](DEMANDAS-API-CLIENTE.md). Prompts antigos não substituem as decisões posteriores de Isabella.

## Código Android já disponível localmente

- Autenticação senha/Google e recuperação via Firebase; sincronização de perfil de negócio pela API, sem nome/telefone de negócio no Firebase.
- Sessão vinculada ao UID e perfil SQL ativo; serviços reais exigem localização autorizada e aparelho com localização ligada.
- Lojas próximas da posição atual, raios 5/10/15/20 km, mapa/lista e destino da unidade no Google Maps.
- Catálogo existente com busca, filtro por loja, paginação e detalhe; ainda não é o feed geográfico definitivo.
- Saldo/histórico por janelas mensais; Impacto usa o saldo real, sem conversão inventada em alimentos ou CO₂. Nível depende do valor oficial retornado.
- Assistente com envio, histórico, lista de conversas, troca/nova conversa e tratamento de erros. Nenhuma resposta local é usada em conta real.
- Imagem HTTPS aprovada no catálogo, placeholder em ausência/falha, sem token Firebase enviado ao provedor de imagens.
- Ajuda e seleção de raio de lojas nesta sessão no Perfil. Edição básica existente depende do contrato de perfil.
- Demonstração somente debug, identificada e isolada das consultas de conta real.

## Falta na integração externa

1. Feed por posição/raio, distância e desconto percentual ordenados no servidor antes da paginação. A consulta atual de promoções não recebe posição/raio.
2. Preferência oficial de raio no cadastro/perfil, inclusive leitura após novo login. O estado atual é apenas da sessão/tela.
3. Crédito/estorno de pontos pelo PDV e CPF, idempotência, tratamento de centavos e nível/status calculado no servidor. Regra confirmada: 1 ponto por real no total gasto; não multiplicar promoções no Android.
4. Avisos online e em segundo plano, no mesmo raio: até três campanhas de produtos diferentes por loja/dia, elegibilidade e liberação antecipada para clientes com mais pontos. Janela/grupo prioritário e fuso precisam ser publicados. Não adicionar FCM: Firebase permanece somente autenticação.
5. Avatar Cloudinary: upload autorizado, confirmação, referência no perfil, exclusão e limites. Não há seletor que finja persistência.
6. Referência de fotos de produto no catálogo. Android já aceita os campos opcionais propostos `imageUrl` e `items[].imageUrl`; falta acordo/publicação pela API.
7. Consumidor autorizado na IA e URL `MOTTAINAI_ASSISTANT_BASE_URL`. Ter o cliente HTTP pronto não comprova que o serviço aceita o token do Cliente.
8. Leitura autorizada de nome/contato de negócio no perfil; o contrato protegido atual não permite apresentar hashes como nome.

## Verificação pendente

63 testes JVM passaram e 60 XMLs/Manifest foram analisados. Isso não substitui assembleDebug, lint, testes de UI e homologação em Android Studio/aparelho com serviços reais. Não houve push/PR desta continuação.

Não há checkout, cashback, resgate nem modo offline de negócio no Cliente. A vitrine direciona ao mercado; pontos representam fidelidade/participação e prioridade de melhores promoções.
