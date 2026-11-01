# Bancos de Dados Mottainai

> Referência de arquitetura e operação · PostgreSQL, MongoDB e Redis · atualização 2026-10-30

## Referências para o tracking centralizado

- [Banco operacional para tracking](tracking/01-banco-operacional-para-tracking.md)
- [Banco analítico para tracking](tracking/02-banco-analitico-para-tracking.md)

Esses documentos definem a leitura correta das entidades físicas, privacidade,
grão analítico e fluxo entre databases. O tracking não deve inferir campos que
não estejam nessas referências ou nos modelos lógicos vinculados.

Na camada relacional, o Mottainai utiliza **dois bancos PostgreSQL independentes**.
Essa separação impede que consultas pesadas de BI concorram com vendas, estoque e operações de
caixa, além de permitir políticas próprias de acesso, retenção e escalabilidade.

| Banco | Schema principal | Responsabilidade | Pode receber escrita da API transacional? |
|---|---|---|---|
| `mottainai_operational` | `mottainai` | Cadastros, usuários, clientes, produtos, estoque, compras, vendas, PDV e auditoria | Sim, pelas roles restritas `mottainai_api`, `mottainai_customer_api` e `mottainai_client_api` |
| `mottainai_analytics` | `mottainai_analytics` | Modelo estrela, histórico, indicadores, BI, previsões e recomendações | Não; somente pipeline de ingestão |

## Regra de integração

Os bancos não usam FK, `dblink` nem transação distribuída entre si. O banco
operacional publica eventos confirmados em `event_queue`. Um pipeline
idempotente valida a versão do evento e carrega dimensões e fatos no analítico.

```text
API / PDV / Apps
       |
       v
mottainai_operational -- event_queue --> pipeline --> mottainai_analytics
       ^                                             |
       |--------- recomendação aprovada via API -----+
```

O banco operacional é a fonte oficial do estado atual. O analítico é a fonte
para histórico, agregações e dashboards. Uma recomendação analítica somente
vira ação operacional depois de passar pela API e pelas regras transacionais.

## Características do banco operacional atual

- produto pertence obrigatoriamente a uma empresa;
- SKU e código de barras são únicos dentro da empresa;
- RLS isola empresa e loja;
- operadores veem somente sua loja; administradores veem lojas da empresa;
- sessões de funcionários são revogáveis e armazenam somente hash do refresh token;
- a role `mottainai_api` não possui login, DDL ou `BYPASSRLS`;
- contexto RLS é validado e limitado à transação;
- views operacionais executam com os privilégios do chamador;
- auditoria é imutável para a API e remove CPF e hashes dos registros JSON;
- dados de busca chegam tokenizados e senhas chegam em BCrypt;
- dados pessoais que precisam ser recuperados usam envelope AES-256-GCM, com chave externa ao banco;
- dados pessoais de funcionário ficam em `employee_private_data`; `employee` mantém apenas HMACs de busca e `app_user` não duplica CPF/e-mail;
- o aplicativo do cliente possui role, views, funções e RLS próprios, isolados da equipe interna;
- exclusão de dados privados é lógica e a FK impede a destruição acidental do envelope cifrado;
- a integração legada conserva apenas metadados e checksum, nunca o payload bruto;
- a RPA usa a role restrita `mottainai_migrator`, contexto por empresa e auditoria ativa;
- a sincronização legado → operacional cifra funcionários antes da persistência e ocorre a cada 30 minutos;
- a API consome views `vw_api_*` com privilégios do chamador e funções transacionais idempotentes;
- compra, movimentação, venda e auditoria usam partições mensais.

## Navegação

| Área | Documento inicial |
|---|---|
| MongoDB da IA | [Coleções, API e operação](mongodb/README.md) |
| Redis de notificações e IA | [Estruturas, API e operação](redis/README.md) |
| Entidades e regras de negócio | [Modelo conceitual](modelo-conceitual/README.md) |
| Tabelas, campos e relacionamentos | [Modelo lógico](model-logico/README.md) |
| Segurança e acesso da API | [Arquitetura de segurança](seguranca/01-arquitetura-de-seguranca.md) |
| Instalação, migrations e manutenção | [Guia operacional](operacao/README.md) |
| Organização dos scripts SQL | [Scripts do banco](script/README.md) |

## Fontes versionadas

- [Mottainai-Banco-Operacional](https://github.com/Mottainai-One/Mottainai-Banco-Operacional)
- [Mottainai-Hub](https://github.com/Mottainai-One/Mottainai-Hub)
- [Mottainai-IA](https://github.com/Mottainai-One/Mottainai-IA)
- [Mottainai-Api-NoSQL](https://github.com/Mottainai-One/Mottainai-Api-NoSQL)
- [Mottainai-Redis-Api](https://github.com/Mottainai-One/Mottainai-Redis-Api)

O código SQL executável permanece no repositório do banco. O Hub mantém a
documentação de arquitetura e não deve ser usado como origem de migrations.
