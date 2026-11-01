# Backup, Monitoramento e LGPD

## Backup e continuidade

| Controle | Recomendação mínima |
|---|---|
| Backup completo | Diário, criptografado e fora do ambiente primário |
| Recuperação ponto no tempo | Ativa para o banco operacional |
| Retenção | Definida com jurídico/fiscal e documentada |
| Teste de restauração | Mensal em ambiente isolado |
| Evidência | Data, duração, RPO/RTO obtidos e responsável |

Uma cópia só é considerada backup depois de uma restauração validada. O banco
analítico pode ser reconstruído a partir dos eventos e da fonte operacional,
mas também deve ter backup para reduzir o tempo de recuperação.

## Monitoramento

Alertar sobre:

- conexões ou autenticações anormais;
- crescimento de falhas e dead letters;
- transações ociosas, locks e consultas acima do timeout;
- partições futuras ausentes ou linhas em partições default;
- alterações de role, grants, policies ou funções `SECURITY DEFINER`;
- aumento de sessões revogadas e tentativas de reutilização de token;
- falha de backup, restauração, ingestão ou reconciliação diária.

## LGPD

CPF, CNPJ de empresário individual, e-mail, telefone, endereço, IP e user agent
podem ser dados pessoais. Aplicam-se os princípios de finalidade, necessidade,
segurança, prevenção e prestação de contas.

- analítico usa chaves anônimas e não replica CPF de cliente/funcionário;
- banco recusa valores pessoais abertos fora dos formatos protegidos;
- auditoria remove recursivamente CPF, documentos, identificadores e hashes do JSON;
- logs e `legacy_sync_record` não armazenam payloads completos da integração;
- nome, CPF, e-mail, telefone, UID externo e endereço de cliente usam tokens SHA-256;
- data de nascimento é minimizada para `birth_year` e consentimentos são versionados;
- exclusão lógica preserva obrigação legal, mas não substitui anonimização;
- solicitações de titular devem respeitar retenção fiscal e trilha de fraude;
- acesso à auditoria deve ser restrito e registrado.

## Resposta a incidente

1. revogar credenciais e sessões afetadas;
2. preservar auditoria, logs e snapshot temporal;
3. identificar empresa, loja, usuário e transações envolvidas;
4. bloquear vetor sem apagar evidência;
5. restaurar ou corrigir dados com migration revisada;
6. registrar causa, impacto, comunicação e ações preventivas.
