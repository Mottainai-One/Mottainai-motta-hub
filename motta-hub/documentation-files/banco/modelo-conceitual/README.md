# Modelo Conceitual — Mottainai

> **Banco Operacional** · PostgreSQL 15+ · versão 2026-10-02
> Abstração de alto nível do domínio de negócio do Mottainai, independente de tecnologia, schemas e colunas.

O **modelo conceitual** descreve **o quê** o sistema representa do ponto de vista do negócio — as **entidades**, seus **papéis** e como elas se **relacionam** — sem entrar em detalhes de implementação física (tabelas, chaves, tipos, schemas). Ele é o ponto de partida para a modelagem e o elo entre a documentação funcional (Scope Statement + Requisitos Funcionais) e o modelo lógico.

## Contexto do projeto

O **Mottainai** é um sistema **SaaS multitenant** de gestão inteligente de estoque para supermercados, com o objetivo central de **reduzir o desperdício de alimentos** (shelf life). Ele une um *motor de inteligência* que prevê rupturas e vencimentos, um ERP varejista completo e apps para o cliente final e o caixa.

O sistema é entregue por **quatro superfícies** distintas:

| Superfície | Público | Papel |
|---|---|---|
| **Site Administrativo** (Web) | Dono / Gerente | Gestão gerencial: dashboards, cadastros, regras, relatórios, contabilidade |
| **App Administrativo** (Mobile) | Estoquista / Gerente | Operação de loja: inventário, avarias, inteligência, reposição |
| **App Cliente** (Mobile) | Consumidor final | Promoções, geolocalização, fidelidade, impacto socioambiental |
| **PDV (Caixa)** | Operador de caixa | Frente de caixa: venda, turnos, pagamentos, fidelidade |

## Conteúdo desta pasta

| Documento | Conteúdo |
|---|---|
| [`README.md`](README.md) | Visão geral e navegação (este arquivo) |
| [`01-visao-geral-e-dominios.md`](01-visao-geral-e-dominios.md) | Visão de negócio, missão, regras centrais e mapa de domínios |
| [`02-entidades-e-relacionamentos.md`](02-entidades-e-relacionamentos.md) | Entidades conceituais, relacionamentos e cardinalidades (ERA) |

## Como navegar

1. Comece pelo **mapa de domínios** em `01-visao-geral-e-dominios.md` para entender os grandes blocos do negócio.
2. Em seguida, explore `02-entidades-e-relacionamentos.md` para ver como as entidades se conectam.
3. Quando quiser o detalhamento físico, siga para o **[Modelo Lógico](../model-logico/README.md)**.

---

*Última atualização: 2026-10-02 · Repositório: `Mottainai-Hub` → `Docs/banco/modelo-conceitual`*
