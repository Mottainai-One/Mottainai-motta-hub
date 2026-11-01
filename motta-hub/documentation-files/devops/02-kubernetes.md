# Kubernetes e caminho para produção

## Estado atual

Kubernetes em AWS é uma direção futura, não um ambiente ativo confirmado nesta revisão. A validação atual usa Docker Compose local/CI. Não foram confirmados manifests Kubernetes de produção ou workflow de deploy em cluster AWS nos clones examinados.

Exemplos antigos de K3s, HPA ou manifests não são evidência de deploy ativo.

## Caminho de evolução

1. Estabilizar Compose compartilhado em servidor privado com HTTPS e segredos QA.
2. Padronizar imagens, healthchecks e configuração externa ao container.
3. Definir arquitetura AWS, rede privada, entrada HTTPS, segredos, observabilidade, backups e orçamento.
4. Criar Helm/Kustomize/manifests depois de aprovar arquitetura e responsáveis.
5. Separar QA/produção por namespace e identidade; definir recursos, probes, autoscaling e egress.
6. Implantar primeiro em QA, testar smoke e rollback.
7. Implantar produção por identidade de privilégio mínimo, imagem imutável e aprovação explícita.

## Critérios mínimos

- Segredos/configuração fora da imagem e Git.
- Processo sem root quando suportado, imagem atualizada e avaliada.
- Requests/limits, probes e rollout adequados.
- TLS, rede, exposição, logs, métricas, alertas e runbook.
- Autoscaling só com métricas disponíveis e limite de custo.
- Backup/restore testados para serviços stateful.
- Rollback praticado e responsável definido.

QA e produção não compartilham credenciais, dados ou namespaces. Não expor bancos sem autenticação, não usar latest como única versão e não chamar deploy de validado sem evidência no cluster de destino. Kubernetes não é requisito para QA Compose local.
