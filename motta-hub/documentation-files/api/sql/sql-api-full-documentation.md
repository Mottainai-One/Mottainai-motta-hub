# Mottainai — Documentação Técnica Completa da API

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Stack Tecnológica](#stack-tecnológica)
3. [Arquitetura de Segurança](#arquitetura-de-segurança)
4. [Fluxos de Autenticação](#fluxos-de-autenticação)
5. [Endpoints Completos](#endpoints-completos)
6. [Detalhes Técnicos](#detalhes-técnicos)
7. [Curiosidades e Boas Práticas](#curiosidades-e-boas-práticas)
8. [Estrutura de Branches](#estrutura-de-branches)
9. [Catálogo de Classes](#catálogo-de-classes)

---

## 🎯 Visão Geral

Este documento descreve a API exposta pelos controllers em `src/main/java/com/institutojf/mottainai/controller`. Em caso de divergência, o código, as interfaces Swagger em `controller/swagger` e a configuração de segurança prevalecem.

- **Versão da API:** `v1`
- **Controllers REST:** 18
- **Operações HTTP mapeadas:** 83
- **Documentação interativa:** `/swagger-ui.html`
- **OpenAPI:** `/api-docs`
- **Migrations Flyway:** 9 (`V1` a `V9`)

---

## 🛠️ Stack Tecnológica

### Core Framework

| Componente | Versão | Descrição |
|---|---|---|
| **Java** | 21 | Versão LTS com suporte a records, sealed classes e pattern matching |
| **Spring Boot** | 4.0.0 | Framework principal com auto-configuration e production-ready features |
| **Spring Security** | 7.1.0 | Segurança com OAuth2 Resource Server, JWT e Firebase integration |
| **Spring Data JPA** | 4.0.0 | Persistência com Hibernate 6.4+ |
| **Spring Cloud** | 2025.1.2 | Ecossistema de microserviços (OpenFeign para comunicação entre serviços) |
| **PostgreSQL** | 15+ | Banco relacional com schema `mottainai` |
| **Flyway** | 10.x | Migrations versionadas e imutáveis |
| **Lombok** | 1.18.x | Redução de boilerplate (@Getter, @Setter, @Builder) |
| **Jakarta Validation** | 3.0 | Validação de beans com @Valid, @NotNull, @Email |

### Integrações Externas

| Componente | Uso |
|---|---|
| **RestClient** | Cliente HTTP moderno do Spring para integração com serviços externos (BrasilAPI para CEP) |
| **BrasilAPI** | Serviço externo para consulta de endereços via CEP (com cache Caffeine) |
| **Firebase Authentication** | Autenticação de clientes via JWT Firebase |
| **SpringDoc OpenAPI** | 3.0.3 — Geração automática de documentação Swagger |
| **Spring Mail** | Envio de emails (recuperação de senha, notificações) |
| **Spring Actuator** | Health checks e métricas (`/actuator/health`) |
| **OpenFeign** | Cliente HTTP declarativo para integração com microserviços (Spring Cloud 2025.1.2) |

### Sistema de Cache

| Componente | Uso |
|---|---|
| **Caffeine** | Cache em memória de alta performance |
| **TTL** | 10 minutos (configurável) |
| **Tamanho máximo** | 10.000 entradas por cache |
| **Cache atual** | CEP (BrasilAPI) |

**Configuração em `CacheConfig.java`:**
- TTL: 10 minutos após escrita
- Máximo: 10.000 entradas
- Estatísticas habilitadas para monitoramento

### Ferramentas de Desenvolvimento

| Ferramenta | Propósito |
|---|---|
| **Lombok** | Geração de getters/setters/builders em compile-time |
| **Spring DevTools** | Hot reload e restart automático em desenvolvimento |
| **Maven** | Build e gerenciamento de dependências |

---

## 🔐 Arquitetura de Segurança

### Modelo de Autenticação Dual

A API implementa **dois mecanismos de autenticação independentes**, cada um com seu próprio `SecurityFilterChain`:

```
┌─────────────────────────────────────────────────────────────────┐
│                        SecurityConfig                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FilterChain 1: /api/v1/client/**                         │  │
│  │  ──────────────────────────────────────────────────────── │  │
│  │  • JWT Firebase (Google JWK Set)                          │  │
│  │  • Validação de audience (project-id)                     │  │
│  │  • Stateless session                                      │  │
│  │  • Exige: authenticated                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FilterChain 2: /api/v1/** (resto)                        │  │
│  │  ──────────────────────────────────────────────────────── │  │
│  │  • JWT HS256 (nimbus-jose-jwt)                            │  │
│  │  • Validação de issuer + tokenVersion                     │  │
│  │  • Stateless session                                      │  │
│  │  • Roles: ADMINISTRATOR, MANAGER                          │  │
│  │  • Endpoints públicos: login, forgot-password,            │  │
│  │    reset-password, swagger, actuator/health               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Matriz de Permissões

| Nível | Descrição | Endpoints |
|---|---|---|
| **Público** | Sem autenticação | `/api/v1/auth/login`, `/forgot-password`, `/reset-password` |
| **JWT Equipe (GET)** | Qualquer usuário autenticado | `GET /api/v1/**` (leitura) |
| **JWT Equipe (WRITE)** | ADMINISTRATOR ou MANAGER | `POST`, `PUT`, `DELETE /api/v1/**` |
| **Administrador** | Apenas ADMINISTRATOR | `@PreAuthorize("hasRole('ADMINISTRATOR')")` |
| **Administrador ou Gerente** | ADMINISTRATOR ou MANAGER da loja | Validação via `retailStoreAccess` |
| **JWT Cliente (Firebase)** | Token Firebase válido | `/api/v1/client/**` |

---

## 🔄 Fluxos de Autenticação

### Fluxo 1: Login de Funcionário (JWT HS256)

```
┌──────────┐                              ┌──────────┐                    ┌──────────────┐
│  Cliente │                              │  Server  │                    │  PostgreSQL  │
└────┬─────┘                              └────┬─────┘                    └──────┬───────┘
     │                                          │                                  │
     │  1. POST /api/v1/auth/login              │                                  │
     │     { email, password }                  │                                  │
     ├─────────────────────────────────────────>│                                  │
     │                                          │  2. Buscar usuário ativo         │
     │                                          ├─────────────────────────────────>│
     │                                          │  3. Retornar AppUser + Employee  │
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  4. Verificar senha (BCrypt)     │
     │                                          │                                  │
     │                                          │  5. Gerar JWT HS256              │
     │                                          │     - issuer: mottainai.local    │
     │                                          │     - subject: email             │
     │                                          │     - roles: [ADMINISTRATOR]     │
     │                                          │     - tokenVersion: 3            │
     │                                          │     - exp: 60min                 │
     │                                          │                                  │
     │  6. 200 OK { token, user }               │                                  │
     │<─────────────────────────────────────────│                                  │
     │                                          │                                  │
```

**Detalhes do Token JWT:**
- **Algoritmo:** HS256 (HMAC com SHA-256)
- **Segredo:** Base64-encoded, mínimo 256 bits
- **Claims padrão:** `iss`, `sub`, `exp`, `iat`
- **Claims customizados:** `roles` (array), `tokenVersion` (int)
- **Validação:** Verifica issuer, expiração E tokenVersion do usuário

### Fluxo 2: Validação de Token em Requisições

```
┌──────────┐                              ┌──────────┐                    ┌──────────────┐
│  Cliente │                              │  Server  │                    │  PostgreSQL  │
└────┬─────┘                              └────┬─────┘                    └──────┬───────┘
     │                                          │                                  │
     │  1. GET /api/v1/products                 │                                  │
     │     Authorization: Bearer <jwt>          │                                  │
     ├─────────────────────────────────────────>│                                  │
     │                                          │                                  │
     │                                          │  2. Decodificar JWT (HS256)      │
     │                                          │                                  │
     │                                          │  3. Validar issuer + exp         │
     │                                          │                                  │
     │                                          │  4. tokenVersionValidator()      │
     │                                          ├─────────────────────────────────>│
     │                                          │  SELECT * FROM app_user          │
     │                                          │  WHERE email = ? AND active=true │
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  5. Comparar tokenVersion        │
     │                                          │     JWT: 3 vs DB: 3 ✓            │
     │                                          │                                  │
     │                                          │  6. Verificar role               │
     │                                          │     JWT: ADMINISTRATOR ✓         │
     │                                          │                                  │
     │  7. 200 OK (produtos)                    │                                  │
     │<─────────────────────────────────────────│                                  │
     │                                          │                                  │
```

**Importante:** O `tokenVersionValidator()` invalida tokens antigos quando:
- Senha é alterada (tokenVersion incrementa)
- Usuário é desativado
- Employee é desativado
- Role é desativada

### Fluxo 3: Autenticação de Cliente (Firebase JWT)

```
┌──────────┐                              ┌──────────┐                    ┌──────────────┐
│  Cliente │                              │  Server  │                    │  Google JWK  │
└────┬─────┘                              └────┬─────┘                    └──────┬───────┘
     │                                          │                                  │
     │  1. POST /api/v1/client/loyalty/redeem   │                                  │
     │     Authorization: Bearer <firebase-jwt> │                                  │
     ├─────────────────────────────────────────>│                                  │
     │                                          │                                  │
     │                                          │  2. Decodificar JWT              │
     │                                          ├─────────────────────────────────>│
     │                                          │  GET /service_accounts/v1/jwk    │
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  3. Validar assinatura (RS256)   │
     │                                          │                                  │
     │                                          │  4. Validar issuer               │
     │                                          │     https://securetoken.google.  │
     │                                          │     com/<project-id>             │
     │                                          │                                  │
     │                                          │  5. Validar audience             │
     │                                          │     audience == <project-id>     │
     │                                          │                                  │
     │  6. 200 OK (redeem concluído)            │                                  │
     │<─────────────────────────────────────────│                                  │
     │                                          │                                  │
```

**Firebase JWT:**
- **Algoritmo:** RS256 (RSA + SHA-256)
- **Chaves públicas:** Google JWK Set (rotacionadas automaticamente)
- **Issuer:** `https://securetoken.google.com/<project-id>`
- **Audience:** Deve conter o `project-id` do Firebase
- **Validação:** Automática via `oauth2ResourceServer` do Spring Security

### Fluxo 4: Recuperação de Senha (Código Numérico)

```
┌──────────┐                              ┌──────────┐                    ┌──────────────┐
│  Cliente │                              │  Server  │                    │  PostgreSQL  │
└────┬─────┘                              └────┬─────┘                    └──────┬───────┘
     │                                          │                                  │
     │  1. POST /api/v1/auth/forgot-password    │                                  │
     │     { email }                            │                                  │
     ├─────────────────────────────────────────>│                                  │
     │                                          │  2. Buscar usuário ativo         │
     │                                          ├─────────────────────────────────>│
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  3. Rate Limiting check          │
     │                                          │     - Último request < 5 min?    │
     │                                          │     - Se sim → erro              │
     │                                          │                                  │
     │                                          │  4. Gerar código 6 dígitos       │
     │                                          │     - BCrypt hash do código      │
     │                                          │  5. Salvar password_reset_token  │
     │                                          │     (expira em 10min)            │
     │                                          ├─────────────────────────────────>│
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  6. Enviar email com código      │
     │                                          │     (6 dígitos numéricos)        │
     │                                          │                                  │
     │  7. 204 No Content                       │                                  │
     │<─────────────────────────────────────────│                                  │
     │                                          │                                  │
     │  8. POST /api/v1/auth/reset-password     │                                  │
     │     { email, code, newPassword }         │                                  │
     ├─────────────────────────────────────────>│                                  │
     │                                          │  9. Buscar usuário + token       │
     │                                          ├─────────────────────────────────>│
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │                                          │  10. Validar token               │
     │                                          │      - Existe?                   │
     │                                          │      - Não expirou? (10min)      │
     │                                          │      - Tentativas < 5?           │
     │                                          │                                  │
     │                                          │  11. Verificar código (BCrypt)   │
     │                                          │      - Match? ✓                  │
     │                                          │      - Se falhou → attempts++    │
     │                                          │                                  │
     │                                          │  12. Validar nova senha          │
     │                                          │      - Mínimo 8 caracteres       │
     │                                          │      - Maiúsculas + minúsculas   │
     │                                          │      - Números + especiais       │
     │                                          │      - Não contém previsíveis    │
     │                                          │                                  │
     │                                          │  13. Hash nova senha (BCrypt)    │
     │                                          │  14. Incrementar tokenVersion    │
     │                                          │  15. Marcar token como usado     │
     │                                          ├─────────────────────────────────>│
     │                                          │<─────────────────────────────────│
     │                                          │                                  │
     │  16. 204 No Content                      │                                  │
     │<─────────────────────────────────────────│                                  │
     │                                          │                                  │
```

**Segurança da Recuperação:**
- **Código:** 6 dígitos numéricos (100000-999999)
- **Rate Limiting:** 1 request a cada 5 minutos por usuário
- **Expiração:** Código expira em 10 minutos
- **Tentativas:** Máximo 5 tentativas de usar o código
- **Constant Timing:** Sempre executa BCrypt (mesmo sem usuário) para evitar timing attacks
- **Token UUID:** Armazena hash BCrypt do código, não o código em plain text
- **Uso único:** Token marcado como usado após reset bem-sucedido
- **Nova senha:** Validação rigorosa contra termos previsíveis
- **Token Invalidation:** `tokenVersion` incrementa → invalida todos os JWTs anteriores

**Constantes de Segurança:**
```java
private static final int RATE_LIMIT_MINUTES = 5;
private static final int RESET_CODE_EXPIRATION_MINUTES = 10;
private static final int MAX_RESET_ATTEMPTS = 5;
```

**Requisitos de Senha:**
- Mínimo 8 caracteres
- Pelo menos uma letra maiúscula
- Pelo menos uma letra minúscula
- Pelo menos um número
- Pelo menos um caractere especial (!@#$%^&*()_+{}[]:;<>,.?/~)
- Não contém termos previsíveis (configurável via `PREDICTABLE_PASSWORD_TERMS`)

**Termos previsíveis padrão:** `mottainai`, `2026`

---

## 📡 Endpoints Completos

### Autenticação — 3 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| POST | `/api/v1/auth/login` | 200 `TokenResponse` | Público |
| POST | `/api/v1/auth/forgot-password` | 204 sem corpo | Público |
| POST | `/api/v1/auth/reset-password` | 204 sem corpo | Público |

### Perfil e usuários de loja — 6 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/users/me` | 200 `UserResponse` | JWT equipe |
| GET | `/api/v1/stores/me` | 200 `RetailStoreResponse` | JWT equipe |
| GET | `/api/v1/store-users` | 200 `List<UserResponse>` | Administrador |
| GET | `/api/v1/store-users/{id}` | 200 `UserResponse` | Administrador |
| POST | `/api/v1/store-users/invite` | 201 `InviteStoreUserResponse` | Administrador |
| PATCH | `/api/v1/store-users/{id}` | 200 `UserResponse` | Administrador |

### Empresas, lojas, endereços e planos — 19 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/companies` | 200 `Page<CompanyResponse>` | Administrador |
| GET | `/api/v1/companies/{id}` | 200 `CompanyResponse` | Administrador |
| POST | `/api/v1/companies` | 201 `CompanyResponse` | Administrador |
| PUT | `/api/v1/companies/{id}` | 200 `CompanyResponse` | Administrador |
| DELETE | `/api/v1/companies/{id}` | 204 sem corpo | Administrador |
| GET | `/api/v1/stores` | 200 `Page<RetailStoreResponse>` | Administrador |
| GET | `/api/v1/stores/{id}` | 200 `RetailStoreResponse` | Administrador ou gerente da própria loja |
| POST | `/api/v1/stores` | 201 `RetailStoreResponse` | Administrador |
| PUT | `/api/v1/stores/{id}` | 200 `RetailStoreResponse` | Administrador ou gerente da própria loja |
| DELETE | `/api/v1/stores/{id}` | 204 sem corpo | Administrador |
| GET | `/api/v1/addresses` | 200 `Page<AddressResponse>` | JWT equipe |
| GET | `/api/v1/addresses/{id}` | 200 `AddressResponse` | JWT equipe |
| POST | `/api/v1/addresses` | 201 `AddressResponse` | JWT equipe; administrador ou gerente |
| PUT | `/api/v1/addresses/{id}` | 200 `AddressResponse` | JWT equipe; administrador ou gerente |
| GET | `/api/v1/subscription-plans` | 200 `Page<SubscriptionPlanResponse>` | Administrador |
| GET | `/api/v1/subscription-plans/{id}` | 200 `SubscriptionPlanResponse` | Administrador |
| POST | `/api/v1/subscription-plans` | 201 `SubscriptionPlanResponse` | Administrador |
| PUT | `/api/v1/subscription-plans/{id}` | 200 `SubscriptionPlanResponse` | Administrador |
| DELETE | `/api/v1/subscription-plans/{id}` | 204 sem corpo | Administrador |

> Não há endpoint `DELETE /api/v1/addresses/{id}`.

### Catálogo — 21 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/products` | 200 `Page<ProductResponse>` | JWT equipe |
| GET | `/api/v1/products/{id}` | 200 `ProductResponse` | JWT equipe |
| GET | `/api/v1/products/barcode/{barcode}` | 200 `ProductResponse` | JWT equipe |
| POST | `/api/v1/products` | 201 `ProductResponse` | Administrador ou gerente |
| PUT | `/api/v1/products/{id}` | 200 `ProductResponse` | Administrador ou gerente |
| DELETE | `/api/v1/products/{id}` | 204 sem corpo | Administrador ou gerente |
| GET | `/api/v1/product-categories` | 200 `Page<ProductCategoryResponse>` | JWT equipe |
| GET | `/api/v1/product-categories/{id}` | 200 `ProductCategoryResponse` | JWT equipe |
| POST | `/api/v1/product-categories` | 201 `ProductCategoryResponse` | Administrador ou gerente |
| PUT | `/api/v1/product-categories/{id}` | 200 `ProductCategoryResponse` | Administrador ou gerente |
| DELETE | `/api/v1/product-categories/{id}` | 204 sem corpo | Administrador ou gerente |
| GET | `/api/v1/suppliers` | 200 `Page<SupplierResponse>` | JWT equipe |
| GET | `/api/v1/suppliers/{id}` | 200 `SupplierResponse` | JWT equipe |
| POST | `/api/v1/suppliers` | 201 `SupplierResponse` | Administrador ou gerente |
| PUT | `/api/v1/suppliers/{id}` | 200 `SupplierResponse` | Administrador ou gerente |
| DELETE | `/api/v1/suppliers/{id}` | 204 sem corpo | Administrador ou gerente |
| GET | `/api/v1/supplier-products` | 200 `Page<SupplierProductResponse>` | JWT equipe |
| GET | `/api/v1/supplier-products/{id}` | 200 `SupplierProductResponse` | JWT equipe |
| POST | `/api/v1/supplier-products` | 201 `SupplierProductResponse` | Administrador ou gerente |
| PUT | `/api/v1/supplier-products/{id}` | 200 `SupplierProductResponse` | Administrador ou gerente |
| DELETE | `/api/v1/supplier-products/{id}` | 204 sem corpo | Administrador ou gerente |

### Inventário e lotes — 12 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/inventory?storeId={storeId}` | 200 `List<InventoryResponse>` | JWT equipe; escopo validado no serviço |
| GET | `/api/v1/inventory/{id}` | 200 `InventoryResponse` | JWT equipe; escopo validado no serviço |
| POST | `/api/v1/inventory` | 201 `InventoryResponse` | Administrador ou gerente; escopo validado no serviço |
| PUT | `/api/v1/inventory/{id}` | 200 `InventoryResponse` | Administrador ou gerente; escopo validado no serviço |
| DELETE | `/api/v1/inventory/{id}` | 204 sem corpo | Administrador ou gerente; escopo validado no serviço |
| GET | `/api/v1/inventory/barcode/{barcode}?storeId={storeId}` | 200 `List<InventoryResponse>` | JWT equipe; escopo validado no serviço |
| GET | `/api/v1/inventory/expiring?storeId={storeId}&days=30` | 200 `List<InventoryResponse>` | JWT equipe; escopo validado no serviço |
| GET | `/api/v1/inventory/{id}/movements` | 200 `List<InventoryMovementResponse>` | JWT equipe; escopo validado no serviço |
| POST | `/api/v1/inventory/{id}/movements` | 201 `InventoryMovementResponse` | Administrador ou gerente; escopo validado no serviço |
| GET | `/api/v1/batches` | 200 `List<BatchResponse>` | JWT equipe; escopo validado no serviço |
| GET | `/api/v1/batches/{id}` | 200 `BatchResponse` | JWT equipe; escopo validado no serviço |
| POST | `/api/v1/batches` | 201 `BatchResponse` | Administrador ou gerente; escopo validado no serviço |

> Não há `PUT` nem `DELETE` para `/api/v1/batches`.

### Alertas, sugestões e promoções — 18 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/alerts?storeId={storeId}` | 200 `List<AlertResponse>` | JWT equipe |
| GET | `/api/v1/alerts/{id}` | 200 `AlertResponse` | JWT equipe |
| POST | `/api/v1/alerts` | 201 `AlertResponse` | Administrador ou gerente |
| POST | `/api/v1/alerts/{id}/resolve` | 200 `AlertResponse` | Administrador ou gerente |
| GET | `/api/v1/suggestions?storeId={storeId}` | 200 `List<SuggestedActionResponse>` | JWT equipe |
| GET | `/api/v1/suggestions/{id}` | 200 `SuggestedActionResponse` | JWT equipe |
| POST | `/api/v1/suggestions` | 201 `SuggestedActionResponse` | Administrador ou gerente |
| POST | `/api/v1/suggestions/{id}/approve` | 200 `SuggestedActionResponse` | Administrador ou gerente |
| POST | `/api/v1/suggestions/{id}/reject` | 200 `SuggestedActionResponse` | Administrador ou gerente |
| GET | `/api/v1/promotions?storeId={storeId}` | 200 `List<PromotionResponse>` | JWT equipe; escopo validado no serviço |
| GET | `/api/v1/promotions/{id}` | 200 `PromotionResponse` | JWT equipe; escopo validado no serviço |
| POST | `/api/v1/promotions` | 201 `PromotionResponse` | Administrador ou gerente; escopo validado no serviço |
| PUT | `/api/v1/promotions/{id}` | 200 `PromotionResponse` | Administrador ou gerente; escopo validado no serviço |
| POST | `/api/v1/promotions/{id}/activate` | 200 `PromotionResponse` | Administrador ou gerente; escopo validado no serviço |
| POST | `/api/v1/promotions/{id}/deactivate` | 200 `PromotionResponse` | Administrador ou gerente; escopo validado no serviço |
| GET | `/api/v1/promotions/{promotionId}/items` | 200 `List<PromotionItemResponse>` | JWT equipe; escopo validado no serviço |
| POST | `/api/v1/promotions/{promotionId}/items` | 201 `PromotionItemResponse` | Administrador ou gerente; escopo validado no serviço |
| DELETE | `/api/v1/promotions/{promotionId}/items/{id}` | 204 sem corpo | Administrador ou gerente; escopo validado no serviço |

### CEP — 1 operação

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/cep/{cep}` | 200 `CepResponse` | JWT equipe |

> O CEP é validado com regex `\\d{8}`. O resultado fica em cache por 10 minutos via Caffeine.

### Fidelidade do cliente — 3 operações

| Método | Caminho | Sucesso | Acesso |
|---|---|---:|---|
| GET | `/api/v1/client/loyalty/balance` | 200 `LoyaltyAccountResponse` | JWT cliente (Firebase) |
| GET | `/api/v1/client/loyalty/transactions` | 200 `List<LoyaltyTransactionResponse>` | JWT cliente (Firebase) |
| POST | `/api/v1/client/loyalty/redeem` | 200 sem corpo | JWT cliente (Firebase) |

> Não existem os endpoints `/earn` nem `/rewards` nesta API.

---

## ⚙️ Detalhes Técnicos

### Validação de Senha

A validação de senha é rigorosa e configurável:

```java
private void validateNewPassword(String password) {
    if (password == null || password.length() < 8) {
        throw new BusinessException("Password must be at least 8 characters long");
    }
    if (!hasRequiredCharacterTypes(password)) {
        throw new BusinessException("Password must contain uppercase, lowercase, number and special character");
    }
    if (containsPredictableTerm(password)) {
        throw new BusinessException("Password contains predictable terms");
    }
}
```

**Requisitos:**
- Mínimo 8 caracteres
- Pelo menos uma letra maiúscula
- Pelo menos uma letra minúscula
- Pelo menos um número
- Pelo menos um caractere especial
- Não contém termos previsíveis (configurável via `PREDICTABLE_PASSWORD_TERMS`)

**Termos previsíveis padrão:** `mottainai`, `2026`

### Hash de Senha (BCrypt)

- **Algoritmo:** BCrypt com strength 10 (padrão)
- **Salt:** Gerado automaticamente (16 bytes)
- **Hash:** 60 caracteres (formato: `$2a$10$...`)
- **Resistência:** Protege contra rainbow tables e brute force

### Token Versioning

Cada usuário tem um `tokenVersion` (incrementado a cada mudança de senha). O `tokenVersionValidator()` invalida tokens antigos automaticamente:

```java
private OAuth2TokenValidator<Jwt> tokenVersionValidator() {
    return jwt -> appUserRepository.findByEmailIgnoreCaseAndActiveTrueAndDeletedAtIsNull(jwt.getSubject())
            .filter(user -> hasCurrentTokenVersion(user, jwt))
            .map(user -> OAuth2TokenValidatorResult.success())
            .orElseGet(() -> OAuth2TokenValidatorResult.failure(
                    new OAuth2Error("invalid_token", "Token is no longer valid", null)
            ));
}
```

**Quando o token é invalidado:**
1. Senha é alterada (tokenVersion ++)
2. Usuário é desativado (`active = false`)
3. Employee é desativado (`employee.active = false`)
4. Role é desativada (`employee.role.active = false`)

### Controle de Acesso por Loja

O componente `RetailStoreAccess` valida se o usuário tem permissão na loja específica:

```java
public Integer resolveStoreId(Authentication authentication, Integer requestedStoreId) {
    AppUser user = currentUser(authentication);
    Integer userStoreId = user.getEmployee().getStore().getId();
    
    if (isAdministrator(user)) {
        if (requestedStoreId == null) {
            throw new BusinessException("Store id is required for administrators");
        }
        return requestedStoreId;
    }
    
    return userStoreId; // Gerentes só acessam sua própria loja
}
```

### CORS Configuration

```java
@Bean
public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();
    configuration.setAllowedOrigins(allowedOrigins);
    configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    configuration.setAllowedHeaders(List.of("Authorization", "Content-Type"));
    configuration.setExposedHeaders(List.of("Location"));
    configuration.setAllowCredentials(false);
    
    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", configuration);
    return source;
}
```

**Origens permitidas:** Configurável via `CORS_ALLOWED_ORIGINS` (separadas por vírgula)

---

## 🔍 Curiosidades e Boas Práticas

### 1. Soft Delete em Todo o Sistema

Nenhuma entidade é fisicamente deletada. Todos os models têm `deletedAt` (LocalDateTime):

```java
@Column(name = "deleted_at")
private LocalDateTime deletedAt;
```

**Vantagens:**
- Auditoria completa
- Possibilidade de restauração
- Integridade referencial preservada

### 2. Paginação com Spring Data

Endpoints de listagem usam `Page<T>` automaticamente:

```java
@GetMapping
public Page<ProductResponse> list(@PageableDefault(size = 20) Pageable pageable) {
    return productService.findAll(pageable).map(productMapper::toResponse);
}
```

**Parâmetros suportados:**
- `page` (0-indexed)
- `size` (default: 20)
- `sort` (ex: `name,asc` ou `price,desc`)

### 3. DTOs Imutáveis com Records

Todos os DTOs são Java Records (imutáveis por design):

```java
public record CreateProductRequest(
    @NotBlank String name,
    @NotNull BigDecimal price,
    @Size(max = 500) String description
) {}
```

**Vantagens:**
- Thread-safe
- Menos boilerplate
- Validação automática com `@Valid`

### 4. Mappers Explícitos (sem MapStruct)

Os mappers são classes simples, não gerados automaticamente:

```java
@Component
public class ProductMapper {
    public ProductResponse toResponse(Product product) {
        return new ProductResponse(
            product.getId(),
            product.getName(),
            product.getPrice()
        );
    }
}
```

**Vantagens:**
- Controle total sobre a conversão
- Fácil de debugar
- Sem overhead de reflection

### 5. Validation em Cascata

Validação Jakarta é aplicada em múltiplas camadas:

```java
// DTO
public record CreateProductRequest(
    @NotBlank String name,
    @Positive BigDecimal price
) {}

// Entity
@Entity
public class Product {
    @Column(nullable = false, length = 100)
    private String name;
    
    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;
}
```

### 6. Transaction Management

Serviços usam `@Transactional` explicitamente:

```java
@Transactional
public ProductResponse create(CreateProductRequest request) {
    // Lógica de criação
    return productMapper.toResponse(productRepository.save(product));
}
```

**Boas práticas:**
- `@Transactional(readOnly = true)` em métodos de leitura
- Rollback automático em exceções unchecked
- Propagação default: `REQUIRED`

### 7. Error Handling Centralizado

```java
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiError> handleBusinessException(BusinessException ex) {
        return ResponseEntity.status(ex.getStatus())
                .body(new ApiError(ex.getMessage(), ex.getCode()));
    }
}
```

**Vantagens:**
- Respostas de erro consistentes
- Logs centralizados
- Não expõe stack traces ao cliente

### 8. Open-in-view Desabilitado

```yaml
spring:
  jpa:
    open-in-view: false
```

**Por quê?**
- Evita LazyInitializationException
- Força carregamento explícito ( FetchType.EAGER ou fetch joins)
- Melhor performance (conexões não ficam abertas)

### 9. Schema Validation (ddl-auto: validate)

O Hibernate **não** cria/altera tabelas. Ele apenas valida o schema existente:

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate
```

**Por quê?**
- Migrations são gerenciadas pelo Flyway
- Evita alterações acidentais no schema
- Segurança em produção

### 10. Stateless Sessions

Todas as filter chains são stateless:

```java
.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
```

**Por quê?**
- JWT é auto-contido
- Sem HttpSession
- Escalabilidade horizontal (sem sessões para replicar)

---

## 📦 Persistência e Componentes

A estrutura atual contém 197 arquivos Java de produção em `com.institutojf.mottainai`, incluindo:

| Componente | Quantidade |
|---|---|
| Controllers REST | 18 |
| Controllers Swagger | 17 |
| Services | 20 |
| Repositories | 25 |
| Mappers | 13 |
| DTOs de Request | 32 |
| DTOs de Response | 22 |
| Models (Entities) | 25 |
| Enums | 8 |
| Security Classes | 7 |
| Exception Classes | 4 |
| Handler Classes | 3 |
| Config Classes | 2 |
| **Total** | **197** |

### Migrations Flyway

1. `V1__create_extensions.sql` — Habilita extensões PostgreSQL
2. `V2__create_schema_and_types.sql` — Cria schema e enums
3. `V3__create_core_tables.sql` — Tabelas principais (companies, stores, employees)
4. `V4__create_catalog_tables.sql` — Catálogo (products, categories, suppliers)
5. `V5__create_catalog_indexes.sql` — Índices para performance
6. `V6__add_address_uniqueness.sql` — Unicidade de endereços
7. `V7__make_product_version_not_null.sql` — Ajuste de constraint
8. `V8__enforce_case_insensitive_product_category_name.sql` — Case-insensitive
9. `V9__add_password_reset_tokens.sql` — Tabela de recuperação de senha

---

## 🚀 Verificação Local

Para compilar, testar e executar a aplicação:

```bash
# Compilar
mvn clean compile

# Executar testes
mvn test

# Rodar aplicação
mvn spring-boot:run

# Acessar documentação
open http://localhost:8080/swagger-ui.html
```

**Variáveis de ambiente necessárias:**
```bash
# Banco de Dados (obrigatórias)
DB_URL=jdbc:postgresql://localhost:5432/mottainai
DB_USER=mottainai
DB_PASSWORD=secret

# Segurança (obrigatórias)
JWT_SECRET=<base64-encoded-256-bit-key>           # Obrigatório, mínimo 32 bytes
FIREBASE_PROJECT_ID=<firebase-project-id>          # Obrigatório para auth de clientes

# CORS (opcional, default: vazio = sem CORS)
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT (opcional)
JWT_EXPIRATION_MINUTES=60                          # Default: 60

# Email (opcionais)
MAIL_HOST=localhost                                # Default: localhost
MAIL_PORT=587                                      # Default: 587
MAIL_USERNAME=no-reply@mottainai.local             # Default: no-reply@mottainai.local
MAIL_PASSWORD=

# Senha (opcional)
PREDICTABLE_PASSWORD_TERMS=mottainai,2026          # Default: mottainai,2026

# BrasilAPI (opcional, default: https://brasilapi.com.br/api)
# brasilapi.base-url pode ser configurado via application.yaml
```

> O `application.yaml` também carrega variáveis de um arquivo `.env` opcional via `spring.config.import: optional:file:.env[.properties]`.

---

## 📝 Changelog

**2026-08-30:**
- Documentação completa criada
- Fluxos de autenticação detalhados
- Matriz de permissões documentada
- Curiosidades e boas práticas adicionadas

## 🔀 Estrutura de Branches

### Branches Locais

```
* main                                    # Branch principal
```

### Branches Remotas (Origin)

```
remotes/origin/main
remotes/origin/docs/api-technical-documentation        # Documentação técnica
remotes/origin/feat/ci-pipeline                        # Pipeline de CI/CD
remotes/origin/feature/alerts-and-suggestions          # Sistema de alertas e sugestões
remotes/origin/feature/company-store-management        # Gestão de empresas e lojas
remotes/origin/feature/customer-loyalty                # Programa de fidelidade
remotes/origin/feature/integrate-brasilapi             # Integração com BrasilAPI
remotes/origin/feature/inventory-management            # Gestão de inventário
remotes/origin/feature/password-recovery-v2            # Recuperação de senha v2
remotes/origin/feature/password-validation             # Validação de senhas
remotes/origin/feature/product-catalog-enhancements    # Melhorias no catálogo
remotes/origin/feature/promotions                      # Sistema de promoções
remotes/origin/feature/spring-boot-crud-api            # API CRUD inicial
remotes/origin/feature/store-user-management           # Gestão de usuários
remotes/origin/fix/authentication-security             # Correções de segurança
remotes/origin/fix/authentication-security-v2          # Correções de segurança v2
remotes/origin/fix/password-recovery-v2                # Correções recuperação de senha
```

**Branch Atual:** `main`

---

## 📁 Catálogo de Classes

**Total:** 197 classes Java

### Controllers (35 classes)

**Controllers REST (18):**
- `AddressController` - Gestão de endereços
- `AlertController` - Sistema de alertas
- `AuthenticationController` - Autenticação (login, recuperação de senha)
- `BatchController` - Gestão de lotes
- `CepController` - Consulta de CEP via BrasilAPI
- `CompanyController` - Gestão de empresas
- `InventoryController` - Gestão de inventário
- `LoyaltyController` - Programa de fidelidade
- `ProductCategoryController` - Categorias de produtos
- `ProductController` - Catálogo de produtos
- `PromotionController` - Promoções
- `PromotionItemController` - Itens de promoção
- `RetailStoreController` - Lojas de varejo
- `SubscriptionPlanController` - Planos de assinatura
- `SuggestedActionController` - Ações sugeridas
- `SupplierController` - Fornecedores
- `SupplierProductController` - Produtos de fornecedores
- `UserProfileController` - Perfil de usuário

**Interfaces Swagger (17):**
- `AddressControllerApi`
- `AlertControllerApi`
- `AuthenticationControllerApi`
- `BatchControllerApi`
- `CompanyControllerApi`
- `InventoryControllerApi`
- `LoyaltyControllerApi`
- `ProductCategoryControllerApi`
- `ProductControllerApi`
- `PromotionControllerApi`
- `PromotionItemControllerApi`
- `RetailStoreControllerApi`
- `SubscriptionPlanControllerApi`
- `SuggestedActionControllerApi`
- `SupplierControllerApi`
- `SupplierProductControllerApi`
- `UserProfileControllerApi`

---

### Services (20 classes)

- `AddressService` - Lógica de endereços
- `AlertService` - Lógica de alertas
- `AuthenticationService` - Autenticação e autorização
- `BatchService` - Gestão de lotes
- `BrasilApiService` - Integração com BrasilAPI (CEP com cache Caffeine)
- `CompanyService` - Gestão de empresas
- `InventoryMovementService` - Movimentações de estoque
- `InventoryService` - Gestão de inventário
- `LoyaltyService` - Programa de fidelidade
- `PasswordResetEmailService` - Envio de emails de recuperação
- `ProductCategoryService` - Categorias
- `ProductService` - Catálogo de produtos
- `PromotionItemService` - Itens de promoção
- `PromotionService` - Promoções
- `RetailStoreService` - Lojas
- `SubscriptionPlanService` - Planos de assinatura
- `SuggestedActionService` - Ações sugeridas
- `SupplierProductService` - Produtos de fornecedores
- `SupplierService` - Fornecedores
- `UserProfileService` - Perfil de usuário

---

### Repositories (25 classes)

- `AddressRepository`
- `AlertRepository`
- `AppUserRepository`
- `BatchRepository`
- `CompanyRepository`
- `CustomerRepository`
- `EmployeeRepository`
- `EmployeeRoleRepository`
- `InventoryMovementRepository`
- `InventoryRepository`
- `LoyaltyAccountRepository`
- `LoyaltyRedemptionRepository`
- `LoyaltyRewardRepository`
- `LoyaltyTransactionRepository`
- `PasswordResetTokenRepository`
- `ProductCategoryRepository`
- `ProductRepository`
- `PromotionItemRepository`
- `PromotionRepository`
- `RetailStoreRepository`
- `SubscriptionPlanRepository`
- `SuggestedActionRepository`
- `SupplierProductRepository`
- `SupplierRepository`
- `TaxProfileRepository`

---

### Models/Entities (33 classes)

**Entidades Principais:**
- `Address` - Endereços
- `Alert` - Alertas do sistema
- `AppUser` - Usuários do app (funcionários)
- `Batch` - Lotes de produtos
- `Company` - Empresas
- `Customer` - Clientes
- `Employee` - Funcionários
- `EmployeeRole` - Papéis de funcionários
- `Inventory` - Itens de inventário
- `InventoryMovement` - Movimentações de estoque
- `LoyaltyAccount` - Contas de fidelidade
- `LoyaltyRedemption` - Resgates de fidelidade
- `LoyaltyReward` - Recompensas
- `LoyaltyTransaction` - Transações de fidelidade
- `PasswordResetToken` - Tokens de recuperação de senha
- `Product` - Produtos
- `ProductCategory` - Categorias
- `Promotion` - Promoções
- `PromotionItem` - Itens de promoção
- `RetailStore` - Lojas de varejo
- `SubscriptionPlan` - Planos de assinatura
- `SuggestedAction` - Ações sugeridas
- `Supplier` - Fornecedores
- `SupplierProduct` - Produtos de fornecedores
- `TaxProfile` - Perfis tributários

**Enums (8):**
- `AlertStatus` - Status de alertas
- `AlertType` - Tipos de alertas
- `InventoryType` - Tipos de inventário
- `MovementType` - Tipos de movimentação
- `PriorityLevel` - Níveis de prioridade
- `PromotionStatus` - Status de promoções
- `SuggestedActionStatus` - Status de ações sugeridas
- `SuggestedActionType` - Tipos de ações sugeridas

---

### DTOs (55 classes)

**Request DTOs (32):**
- `CreateAddressRequest`
- `CreateAlertRequest`
- `CreateBatchRequest`
- `CreateCompanyRequest`
- `CreateInventoryMovementRequest`
- `CreateInventoryRequest`
- `CreateLoyaltyRewardRequest`
- `CreateProductCategoryRequest`
- `CreateProductRequest`
- `CreatePromotionItemRequest`
- `CreatePromotionRequest`
- `CreateRetailStoreRequest`
- `CreateSubscriptionPlanRequest`
- `CreateSuggestedActionRequest`
- `CreateSupplierProductRequest`
- `CreateSupplierRequest`
- `ForgotPasswordRequest`
- `InviteStoreUserRequest`
- `LoginRequest`
- `RedeemRewardRequest`
- `ResetPasswordRequest`
- `UpdateAddressRequest`
- `UpdateCompanyRequest`
- `UpdateInventoryRequest`
- `UpdateProductCategoryRequest`
- `UpdateProductRequest`
- `UpdatePromotionRequest`
- `UpdateRetailStoreRequest`
- `UpdateStoreUserRequest`
- `UpdateSubscriptionPlanRequest`
- `UpdateSupplierProductRequest`
- `UpdateSupplierRequest`

**Response DTOs (22):**
- `AddressResponse`
- `AlertResponse`
- `BatchResponse`
- `CepResponse` - Retorno da consulta de CEP (zipCode, street, neighborhood, city, state, service)
- `CompanyResponse`
- `InventoryMovementResponse`
- `InventoryResponse`
- `InviteStoreUserResponse`
- `LoyaltyAccountResponse`
- `LoyaltyRewardResponse`
- `LoyaltyTransactionResponse`
- `ProductCategoryResponse`
- `ProductResponse`
- `PromotionItemResponse`
- `PromotionResponse`
- `RetailStoreResponse`
- `SubscriptionPlanResponse`
- `SuggestedActionResponse`
- `SupplierProductResponse`
- `SupplierResponse`
- `TokenResponse`
- `UserResponse`

---

### Mappers (13 classes)

- `AddressMapper`
- `AlertMapper`
- `BatchMapper`
- `CompanyMapper`
- `InventoryMapper`
- `InventoryMovementMapper`
- `ProductCategoryMapper`
- `ProductMapper`
- `RetailStoreMapper`
- `SubscriptionPlanMapper`
- `SuggestedActionMapper`
- `SupplierMapper`
- `SupplierProductMapper`

---

### Segurança (7 classes)

- `CustomerAccess` - Controle de acesso de clientes
- `DatabaseUserDetailsService` - Service de detalhes de usuário
- `FirebaseProperties` - Configurações Firebase
- `InventoryAccess` - Controle de acesso de inventário
- `JwtProperties` - Configurações JWT
- `JwtService` - Serviço de geração/validação de tokens
- `SecurityConfig` - Configuração principal de segurança

---

### Exceptions (4 classes)

- `BusinessException` - Exceções de negócio
- `ConflictException` - Conflitos de dados
- `CepNotFoundException` - CEP não encontrado na base dos Correios
- `ResourceNotFoundException` - Recurso não encontrado

---

### Handler (3 classes)

- `ApiError` - Estrutura de erro de API
- `FieldError` - Erro de campo específico
- `GlobalExceptionHandler` - Handler global de exceções

---

### Config (2 classes)

- `OpenApiConfig` - Configuração do OpenAPI/Swagger
- `CacheConfig` - Configuração de cache com Caffeine (TTL 10min, máximo 10.000 entradas)

### Application (1 classe)

- `MottainaiApplication` - Classe principal da aplicação (`com.institutojf.mottainai`)

---

**Última atualização:** 2026-08-30

---

## 📞 Suporte

Para dúvidas sobre a API:
- Documentação interativa: `http://localhost:8080/swagger-ui.html`
- OpenAPI spec: `http://localhost:8080/api-docs`
- Health check: `http://localhost:8080/actuator/health`

---

**Mottainai API v1.0** — Construído com ❤️ usando Spring Boot 4.0.0
�o interativa: `http://localhost:8080/swagger-ui.html`
- OpenAPI spec: `http://localhost:8080/api-docs`
- Health check: `http://localhost:8080/actuator/health`

---

**Mottainai API v1.0** — Construído com ❤️ usando Spring Boot 4.0.0
