# 04 — Dados, Serviços e Autenticação

## Limite de integração

O README do projeto informa que o front-end ainda não se conecta a uma API de autenticação ou de dados. A busca no código de `src/` também não encontrou chamadas `fetch` ou `axios`. Portanto, os fluxos descritos nesta seção são demonstrações locais e não devem ser tratados como transações reais do sistema.

Uma integração real de login depende de um serviço de servidor com validação de credenciais e sessão adequada. O endereço e o contrato dessa API não estão definidos neste projeto; por isso o login de produção permanece desativado.

## Autenticação atual

1. `AuthProvider` valida e sanitiza as credenciais antes de chamar `authService.login`.
2. Em desenvolvimento e no modo `lighthouse`, `authService` carrega `mockAuthService`, que cria um token de demonstração.
3. O Provider decodifica o token, atualiza o estado de autenticação e, quando o mock está habilitado, grava a sessão no armazenamento local.
4. `PrivateRoute` consulta o estado fornecido por `useAuth` antes de renderizar as áreas protegidas.
5. Em build normal de produção, `authService.login` informa que a autenticação real não está configurada e o Provider descarta tokens antigos do navegador.

No modo de desenvolvimento, não existe uma conta de demonstração pré-cadastrada: depois da validação do formulário, qualquer e-mail em formato válido com senha não vazia passa pela verificação simulada. O token gerado pelo mock não comprova identidade perante um servidor. Ele existe para demonstrar a navegação e permitir a auditoria local.

## Armazenamento no navegador

| Dado | Mecanismo e chave | Escopo e limite |
|---|---|---|
| Sessão de demonstração | `localStorage`, chave `@App:token`, objeto com `_versao: 1` | Apenas quando o mock está habilitado; token expirado ou inválido é removido |
| Preferências de acessibilidade | `localStorage`, chave `acessibility_v1` | Preferências do navegador atual; valores são sanitizados conforme o schema versão 1 |
| Preferência de relatório gerencial | `localStorage`, chave `relatorios_gerenciais_v1` | Formato selecionado; existe leitura de uma chave legada para migração |
| Relatórios gerenciais salvos | IndexedDB, banco `mottainai-management-reports` | Neste navegador; registros com mais de 365 dias são removidos durante a leitura/gravação |
| Relatórios financeiros mensais | IndexedDB, banco `mottainai-monthly-financial-reports` | Neste navegador; registros com mais de 365 dias são removidos durante a leitura/gravação |

O armazenamento local pode ser apagado pelo navegador ou pela própria pessoa usuária. Não há sincronização com conta ou servidor.

## Dados e serviços demonstrativos

- `src/data/` contém exemplos de produtos, estoque, fornecedores, transferências, contagens e ajustes.
- `historicalMetricService` e `rankingService` retornam conjuntos demonstrativos com atraso simulado e aceitam cancelamento por `AbortSignal`.
- `productDetailsService` combina produtos locais com detalhes e histórico de ação definidos para demonstração.
- `productImportService` simula uma prévia e o cadastro de produtos; não envia o arquivo para um serviço remoto.
- `passwordRecoveryService` simula envio e verificação de código; seu código de demonstração é `123456` e não deve ser usado como mecanismo real de recuperação.
- `managementReportService` e `monthlyFinancialReportService` persistem relatórios localmente no IndexedDB.

## Validação

As validações estão em funções tipadas de `src/utils/`, como `loginValidation.ts`, `productImportValidation.ts`, `supplierFormValidation.ts`, `stockCountValidation.ts` e `transferFormValidation.ts`. As páginas mantêm os erros junto ao estado do formulário e mostram feedback no fluxo da interface.

## Referências

- `src/services/authService.ts` e `src/services/mockAuthService.ts`
- `src/context/AuthProvider.tsx` e `src/pages/PrivateRoute/index.tsx`
- `src/data/`
- `src/services/managementReportService.ts` e `src/services/monthlyFinancialReportService.ts`
- `src/utils/accessibilityPreferences.ts` e `src/services/managementReportPreferencesService.ts`
- `README.md`, seção “Estado da integração”

---

*Próximo: [05 — Interface, Responsividade e Acessibilidade](05-interface-acessibilidade.md).*
