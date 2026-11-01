# Plano de execução — somente Mobile Cliente

> Escopo esclarecido por Isabella em 21/10/2026: esta frente implementa **somente o app Android Cliente**. API Cliente será feita por outra pessoa. API, banco, PDV, IA e infraestrutura são dependências externas, não entregas de código deste agente. Esta definição substitui a atribuição de implementação backend presente no plano anterior do Hub.

## Responsabilidades

- **Nesta frente:** Java/XML, navegação, autenticação Firebase no Android, consumo de contratos publicados, permissões, mapa, exibição de avisos, formulários, DTOs/repositórios/ViewModels, estados de erro/vazio/carregamento e testes do mobile.
- **Equipe da API/integrações:** persistência e autorização de negócio, geografia/ordenação paginada, crédito/estorno e status, prioridade/quota de avisos, assinatura/validação de avatar e acesso consumidor à IA.
- **Isabella/QA:** configurações privadas do app, compilação e validação Android Studio/aparelho, aprovação de envio. Não abrir PR nem fazer push sem confirmação, inclusive quando o push dispara o bot.
- O mobile não acessa SQL diretamente, não cria serviços paralelos e não inventa endpoints para aparentar conclusão. Não implementar cálculos oficiais no Android quando pertencem à API.

Documento para encaminhamento externo: [DEMANDAS-API-CLIENTE.md](DEMANDAS-API-CLIENTE.md).

## Etapas revisáveis

| Entrega mobile | Estado local | Dependência / próximo aceite |
| --- | --- | --- |
| Firebase somente autenticação e sessão vinculada ao perfil SQL | Alterações locais existentes | Homologar senha/Google, sincronização, perfil inativo e troca de conta |
| Google Maps oficial com unidade da oferta | Implementado localmente | Testar app Maps instalado/ausente, alternativa web e destino incompleto |
| Raios 5/10/15/20 km na consulta de lojas | Implementado localmente | Validar paginação, mudança de raio e recriação de tela |
| Bloqueio de serviços por sessão/localização | Implementado localmente | Validar recusa permanente, GPS desligado, retorno de configurações e saída |
| Contexto de lojas Home/mapa compartilhado | Implementado localmente | Leitura automática ao entrar/retornar, atualização manual, timeout/cancelamento; validar em aparelho, sem posição persistida |
| Raio na confirmação do endereço e preferência oficial | Pendente | Campo/rota de criação, leitura e atualização publicados pela API |
| Home/Catálogo de ofertas próximas | Pendente | Consulta geográfica ordenada antes de paginar; não filtrar uma página global no app |
| Permissões/canal de avisos e geofencing em segundo plano | Pendente | Contrato de regiões, ofertas elegíveis, autorização/quota e política de liberação por fidelidade |
| Pontos/histórico/status reais | Consulta de saldo/histórico existente; restante pendente | API PDV/CPF/crédito/estorno e tipos/status oficiais; Android apenas apresenta |
| Nome e contato oficiais no Perfil | Edição parcial existente; leitura legível pendente | Representação autorizada publicada pela API, sem usar hashes ou Firebase display name |
| Avatar Cloudinary | Pendente | Fluxo autorizado de upload, confirmação e leitura da referência |
| Foto do produto na oferta | Carregamento HTTPS e placeholder implementados | API precisa publicar/aprovar os campos opcionais de referência de imagem |
| Assistente real | Cliente HTTP, envio, histórico e conversas implementados | Configurar URL da IA e homologar consumidor autorizado/isolamento entre contas |
| Impacto e compartilhamento | Saldo real implementado, sem métricas ambientais fictícias | Nível/progresso dependem de campos oficiais opcionais no saldo |
| Perfil: ajuda e raio da sessão | Implementado localmente | Raio oficial persistido e avatar ainda dependem da API |
| Homologação final | Pendente | Build/lint/testes, aparelho, integração com ambiente compatível e cenários de permissões |

Essas linhas são unidades propostas de revisão, não PRs abertas. Preservar trabalho local anterior; separar normalmente em 1–3 commits relacionados somente quando sua preparação for autorizada. Branches novas devem usar `feat/` ou `fix/`, nunca `codex/`.

## Ordem prática

1. Homologar a base Android local e corrigir falhas observadas nas telas/permissões.
2. Receber contrato de raio/perfil e feed geográfico; então integrar cadastro, Home e Catálogo.
3. Receber elegibilidade/quota de avisos; integrar permissões contextuais e geofencing/background, sem prometer entrega instantânea.
4. Integrar saldo/histórico/status calculados pelo servidor quando compra/estorno estiverem publicados.
5. Integrar perfil, avatar, imagem e chat à medida que cada contrato estiver pronto; não precisam formar uma única stack.
6. Aceitar cada etapa com evidência real e preparar a versão final. Sem implementação/ambiente externo, registrar dependência; não declarar funcionalidade completa por existir uma tela.

## Evidência atual e limites

- 63 testes JVM aprovados e 60 XMLs/Manifest analisados na etapa mais recente: acesso, raio, coordenadas, Maps, CPF, perfil, paginação, períodos, demonstração, apresentação de pontos, contratos do chat e imagens.
- Compilação direta de partes do núcleo foi feita; Activities/Fragments novos, APK, lint e UI ainda precisam de validação no Android Studio.
- Nesta rodada, compilação Java direta também validou ApiClient, AssistantService, Offer, ProductImages, OfferAdapter e ProfileFragment contra bibliotecas Android locais e artefatos gerados existentes. Esse recorte não recompila recursos, não valida todas as Activities e não equivale a um build Gradle.
- Nada dessa continuação foi enviado por push ou aberto em PR.
- Sem alteração de código de API, PDV, IA, banco ou infraestrutura nesta frente.
- Referências locais: [guia](../MOBILE-CLIENTE.md), [acesso/localização](location-access.md), [catálogo](catalog.md) e [autenticação](authentication.md).
- Roteiro de aceite e bloqueios: [TESTES-ENTREGA-CLIENTE.md](TESTES-ENTREGA-CLIENTE.md).
