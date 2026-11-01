# Autenticação e retomada do cadastro

> Atualização local de 20/10/2026: Firebase somente para autenticação e Cliente sem offline. A gravação/leitura do nome no perfil Firebase foi removida nesta branch. A leitura do nome de negócio pelo backend continua pendente; veja [MOBILE-CLIENTE.md](../MOBILE-CLIENTE.md). Não houve publicação desta entrega.

Firebase Authentication fornece a identidade por e-mail/senha ou Google. O app envia o Firebase ID token à API; o backend valida o token e associa o UID ao perfil SQL. O Operacional mantém seu fluxo de autenticação próprio.

## Contratos existentes

- `GET /api/v1/client/auth/profile`: perfil do Firebase UID autenticado; `404` significa cadastro SQL ausente.
- `POST /api/v1/client/auth/profile`: cria o perfil de negócio; a API existente retorna o perfil já associado ao mesmo UID em repetições.
- `PUT /api/v1/client/auth/profile`: atualiza nome, telefone e consentimento do próprio cliente.

O Android só ativa uma nova sessão após receber HTTP `200`/`201`, ID SQL positivo e `active=true`. Perfil ausente, incompleto, inativo, `202` ou `204` não libera o acesso. Salva o ID SQL junto ao UID Firebase, sem token ou senha. Sessões anteriores sem UID precisam de nova sincronização. Essas checagens não substituem a autorização do servidor.

A API inspecionada mantém o contrato protegido: ID, ano de nascimento, situação e consentimento, sem nome/e-mail/telefone em texto aberto. O app não usa `getDisplayName` nem atualiza o perfil Firebase. O e-mail de acesso continua vindo da identidade autenticada. Sem nome autorizado, Perfil mostra “Cliente” e Home usa saudação neutra. Após uma edição SQL confirmada, o nome enviado pode ser mostrado em memória; nova leitura protegida não o recupera. Os campos de apresentação são transitórios, excluídos de JSON, e não interpretam tokens protegidos como nomes.

O formulário explica que é necessário informar o nome para editar, pois o PUT existente exige `fullName`. Isso não é uma solução definitiva de leitura do perfil. O app omite `phone` para manter o valor existente; essa semântica depende da correção da API na branch `fix/customer-profile-update`, ainda a conferir no ambiente implantado.

## Comportamento

1. E-mail/senha e Google seguem a mesma consulta de perfil.
2. Em `404`, abrir a conclusão do cadastro com a identidade já autenticada; não pedir outra senha nem criar outra conta Firebase.
3. Em falha de rede ou servidor, manter a identidade Firebase e oferecer “Tentar sincronizar novamente”.
4. Se a conta Firebase foi criada e o POST SQL falhou, o envio pode ser repetido com a mesma identidade. Fechar e abrir o app também permite retomar pelo login.
5. Para nova conta por senha, pedir confirmação da senha. O formulário de cadastro tem duas etapas e preserva a etapa na recriação da tela; senhas não são incluídas no estado salvo.
6. “Esqueci minha senha” usa o Firebase e não depende da API SQL. A confirmação usa mensagem genérica, sem confirmar a existência de um e-mail.
7. Uma resposta de autenticação/perfil atrasada não pode ativar a sessão de outro Firebase UID.
8. Um `401` permite no máximo uma repetição de autenticação. Falhas de rede não fazem logout. Se um token renovado continuar rejeitado pela API, limpar a associação SQL e retornar ao login; a identidade Firebase permanece disponível para nova sincronização.

## Roteiro no Android Studio

- Cadastro valida os dois dígitos verificadores do CPF e rejeita sequências repetidas antes de criar/enviar o perfil. `CpfValidatorTest` cobre formatos, zeros à esquerda e erros nos verificadores. Isso não consulta a Receita, não comprova titularidade nem substitui validação/uniquidade na API. Referência do conceito de validação CPF: [Hibernate Validator](https://docs.jboss.org/hibernate/validator/6.1/reference/en-US/html_single/#validator-defineconstraints-spec).
- Conta com perfil SQL: testar senha e Google, fechar/reabrir o app e conferir identidade no perfil.
- Conta Firebase sem perfil SQL: ambos os métodos abrem a conclusão do cadastro, com e-mail bloqueado e campos de senha ocultos.
- Interromper a API depois de criar a conta Firebase; restaurar a API e repetir o envio. Deve existir somente um perfil para o UID.
- Falhar a leitura do perfil depois de autenticar; o botão de sincronização deve recuperar sem criar conta nem exigir outra autenticação.
- Retornar do cadastro e girar a tela em cada etapa. Conferir campos, etapa, mensagens e ausência de navegação repetida.
- Tocar repetidamente em entrar/cadastro/Google. Somente um fluxo deve ficar em andamento.
- Usar “Esqueci minha senha” com API desligada; conferir o e-mail no projeto Firebase configurado.
- Testar rede indisponível, resposta de perfil incompleta, `401`, `403`, `404` e `500`; somente `404` inicia conclusão de cadastro.
- Sair e entrar em outra conta, inclusive com uma consulta anterior em andamento. O perfil e o saldo devem pertencer à nova identidade.
- Confirmar que o modo demonstração continua restrito a debug e não ativa uma sessão real.
- Retornar `active=false` ou omitir `active` em um perfil de teste: não deve abrir sessão. Uma consulta que confirme perfil inativo limpa a associação SQL local.
- Cadastrar e editar com um nome diferente do antigo display name Firebase. O app não deve alterar nem usar esse display name. Conferir apresentação neutra após nova leitura protegida.

## Configuração

A API precisa estar acessível no endereço configurado em `MOTTAINAI_API_BASE_URL`, com o schema SQL e validação do projeto Firebase do Cliente. O Android precisa do `google-services.json`, dos provedores habilitados e das impressões digitais corretas para Google Sign-In. Falha de conexão com a API não é corrigida apenas pela configuração do Firebase.

Compilação e roteiro no emulador/aparelho ficam com Isabella. O teste unitário `ProfileSyncStatusTest` cobre a decisão de acesso/conclusão/erro sem depender de Firebase ou rede.
