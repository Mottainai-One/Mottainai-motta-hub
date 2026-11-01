# Aceite do Mobile Cliente

> Estado em 21/10/2026: implementação local, ainda não é APK homologado. Nenhum push/PR foi feito nesta continuação. Apenas Mobile Cliente foi alterado.

## Preparar o teste

1. Abrir este checkout `Mottainai-Mobile-Cliente-work` no Android Studio, não confundir com o original em StudioProjects.
2. Manter `app/google-services.json` e propriedades privadas fora do Git. Firebase deve aceitar o pacote/certificado e provedores senha/Google.
3. Configurar `MOTTAINAI_API_BASE_URL`, `MOTTAINAI_MAPS_API_KEY` e, para IA real, `MOTTAINAI_ASSISTANT_BASE_URL` nas propriedades pessoais do Gradle. Não usar o exemplo com placeholder como endereço real.
4. Sincronizar dependências, compilar `assembleDebug`, executar `lint` e `test`. Esta rodada não executou essas tarefas; a evidência disponível é a verificação JVM direta de 63 testes e análise de 60 XMLs/Manifest.
5. Usar ambiente/API e contas de teste autorizadas. Ausência do servidor não será corrigida alterando login ou liberando acesso anônimo.

## Roteiro de aparelho/emulador

| Área | Conferir |
| --- | --- |
| Login/cadastro | Senha, Google, recuperação, CPF inválido, cadastro em etapas, perfil ausente/inativo, erro e nova tentativa sem duplicar Firebase |
| Sessão | Logout, reentrada, troca de conta, refresh limitado; nenhum dado da primeira conta aparece na segunda |
| Acesso | Negar localização, negar permanentemente, GPS desligado, localização aproximada, voltar das configurações; sem loop de permissões |
| Lojas | Posição atual, timeout, erro, vazio, raios 5/10/15/20, troca de raio durante consulta, paginação e retorno após background |
| Mapa | Pins da mesma lista, loja sem coordenada, destino da unidade, Maps instalado/ausente e endereço insuficiente |
| Catálogo | Busca, filtro por loja, páginas sem duplicação, detalhe removido, falha/retry independente da Home |
| Imagens | URL HTTPS aprovada, ausente, inválida, 404 e rolagem rápida; imagem de card anterior não pode permanecer |
| Pontos | Saldo nulo, real e erro; histórico vazio, meses, falha parcial e nova tentativa; sem crédito calculado no Android |
| Impacto | Mesmo saldo de Pontos, status ausente/oficial, erro e compartilhar apenas saldo confirmado; sem kg/CO₂ inventados |
| Perfil | Editar/salvar/falhar, manter formulário, cancelamento, ajuda, raio identificado como temporário, logout com confirmação |
| Chat | Configuração ausente, consumidor autorizado, envio por botão/teclado, rotação durante request, histórico, conversa encerrada, nova conversa |
| Isolamento IA | Outra conta não acessa conversa anterior; resposta com ID diferente é rejeitada; 401 exclusivo da IA não encerra sessão SQL |
| Rede chat | Desconexão durante envio, atualizar histórico antes de repetir, 403 e 429; sem resposta fictícia em conta real |
| Demo debug | Avisos explícitos, sem GPS/API reais; nunca usada como acesso de produção |

## Ainda não pode ser aceito como concluído

- Ofertas por proximidade/percentual global antes da paginação e preferência de raio persistida: contrato externo ainda necessário.
- Avisos em segundo plano, quota de três produtos/loja/dia e prioridade: implementação Android e integração dependem do fluxo externo de elegibilidade/quota.
- Avatar persistido no Cloudinary: fluxo autorizado ainda necessário; não há upload concluído no app.
- Crédito/estorno por CPF/PDV, status calculado e prioridade: só podem ser comprovados com a implementação externa correspondente.
- Fotos/status opcionais e IA: código consumidor preparado não significa contrato já publicado ou autorização homologada.

Encaminhar [DEMANDAS-API-CLIENTE.md](DEMANDAS-API-CLIENTE.md) à equipe responsável. O app não faz SQL direto, não usa Firestore/Storage/FCM e não cria negócio offline para esconder essas dependências.
