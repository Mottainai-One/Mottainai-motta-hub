# Cloud e serviços hospedados

## Inventário por estado

| Serviço | Uso/estado | Observação |
|---|---|---|
| Aiven PostgreSQL | Bancos operacional e analítico | Plano Free informado pela equipe; não presumir SLA ou capacidade produtiva |
| Databricks Free Edition | Camadas medalhão e BI | Ambiente acadêmico, sem garantia de SLA |
| Render | render.yaml do PR Bot declara serviço | Arquivo não prova deploy ativo ou uso como produção |
| GitHub Actions | CI e workflows de sincronização | Secrets separados por repositório/ambiente |
| AWS | Alvo futuro para produção | Não há hospedagem ativa confirmada; definir arquitetura/custo antes |
| QA compartilhado | Sem servidor, domínio ou HTTPS confirmado | Compose pode ser local; acesso para toda equipe exige implantação |

## Ambientes

Local/QA usa Compose, dados sintéticos e credenciais exclusivas; não acessa produção.

Aiven e Databricks Free apoiam experimentação acadêmica e estão sujeitos a cotas, compute, conectividade e suspensão. Não declarar alta disponibilidade, SLA ou recuperação testada sem evidência.

Produção AWS requer redes, identidade, secrets, backup, observabilidade, orçamento, processo de mudança e recuperação definidos. Decisão de EKS ou alternativa deve ser ADR anterior ao deploy.

## Segredos

Guardar credenciais nos mecanismos do provedor: GitHub Actions Secrets, Render, Databricks Connections/Secrets ou solução AWS aprovada. Usar identidades separadas e privilégio mínimo. Rotacionar segredo exposto. Não inserir valores em YAML, imagem, logs, URLs ou documentação.

## Evidência de implantação

Registrar provedor/ambiente, commit, execução de deploy, URL/healthcheck, permissões, smoke test, responsável, runbook, limites/custo e rollback. Sem essa evidência, marcar como configuração, protótipo ou plano.
