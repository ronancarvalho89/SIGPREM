# SIGPREM

## Visão Geral

Breve descrição do propósito do sistema.

## Objetivos

Objetivos gerais do ERP.

## Arquitetura

Descrição resumida da arquitetura adotada.

### Arquitetura em Camadas

O SIGPREM organiza o backend em camadas com responsabilidades bem definidas:

- **API** — recebe as requisições HTTP, valida parâmetros de entrada, autentica o usuário e delega a execução ao Service correspondente, sem conter regras de negócio.
- **Service** — concentra as regras de negócio, orquestra integrações entre módulos e controla o fluxo transacional da operação.
- **Repository** — realiza exclusivamente o acesso a dados (consultas, persistência e soft delete), sem regras de negócio.
- **Model** — representa as entidades e o mapeamento ORM com o banco de dados.
- **Schema** — define os contratos de entrada e saída da API (validação e serialização).

### Fluxo de Execução

O fluxo padrão utilizado pelo sistema é:

```text
Request
↓
API
↓
Service
↓
Repository
↓
Database
↓
Repository
↓
Service
↓
API
↓
Response
```

### Princípios Arquiteturais

O SIGPREM adota os seguintes princípios:

- Separação de responsabilidades
- Service Layer
- Repository Pattern
- Soft Delete
- Injeção de Dependências
- Transações centralizadas
- Reutilização de regras de negócio
- APIs sem regra de negócio
- Repositories sem regra de negócio
- Services responsáveis pelas regras de negócio

### Estrutura Resumida

```text
app/
├── api/
├── services/
├── repositories/
├── models/
├── schemas/
├── core/

docs/
```

### Objetivos da Arquitetura

A arquitetura foi definida visando:

- facilidade de manutenção;
- facilidade para testes;
- escalabilidade;
- baixo acoplamento;
- alta reutilização de código;
- facilidade de evolução do sistema.

## Estrutura de Pastas

Visão geral da organização do projeto.

## Módulos

Lista dos módulos existentes.

## Fluxos do Sistema

Índice dos principais fluxos operacionais.

### Visão Geral

O SIGPREM é estruturado em processos integrados, nos quais uma operação em um módulo pode refletir automaticamente em outros módulos do sistema, mantendo consistência operacional e financeira.

### Fluxo de Compra

Fluxo conceitual:

```text
Fornecedor
↓
Compra de Concreto
↓
Movimento Financeiro
```

### Fluxo de Produção

Fluxo conceitual:

```text
Compra de Concreto
↓
Produção
↓
Cálculo da Mão de Obra
↓
Movimento de Estoque (ENTRADA)
↓
Movimento Financeiro (CUSTO_PRODUÇÃO)
```

### Fluxo de Venda

Fluxo conceitual:

```text
Venda
↓
Itens da Venda
↓
Validação de Estoque
↓
Movimento de Estoque (SAÍDA)
↓
Movimento Financeiro (VENDA)
```

### Fluxo Financeiro

As movimentações financeiras são originadas automaticamente pelos módulos do sistema (compra, produção e venda), evitando lançamentos inconsistentes ou desconectados da operação.

### Fluxo do Dashboard

O Dashboard consome exclusivamente informações provenientes dos Services, sem acesso direto ao banco de dados, atuando como orquestrador de indicadores já consolidados.

### Princípios dos Fluxos

Todos os fluxos seguem:

- transação única;
- rollback em caso de erro;
- integridade dos dados;
- sincronização entre módulos;
- reutilização de regras de negócio.

## Banco de Dados

Introdução ao modelo de dados.

### Objetivo do Banco de Dados

O banco de dados do SIGPREM é o repositório central das informações operacionais e gerenciais do sistema. Seu propósito é garantir a integridade, a rastreabilidade e a consistência dos dados ao longo dos processos de cadastro, compra, produção, venda, estoque e financeiro.

### Tecnologia Utilizada

A persistência do projeto utiliza **SQLAlchemy** como ORM, com banco **SQLite** na configuração padrão atual (`DATABASE_URL`), adequado ao estágio de desenvolvimento e evolução controlada do SIGPREM.

### Organização das Entidades

Principais entidades e suas responsabilidades funcionais:

- **Usuário** — autenticação e acesso ao sistema.
- **Cliente** — cadastro dos clientes atendidos nas vendas.
- **Fornecedor** — cadastro dos fornecedores relacionados às compras de concreto.
- **Produto** — cadastro dos itens pré-moldados utilizados em produção, estoque e vendas.
- **Compra de Concreto** — registro das aquisições de concreto e do saldo disponível para consumo.
- **Produção** — registro da fabricação de produtos, consumo de concreto e custo de mão de obra.
- **Venda** — cabeçalho das operações comerciais realizadas com clientes.
- **ItemVenda** — detalhamento dos produtos vendidos em cada venda.
- **MovimentoEstoque** — histórico de entradas e saídas de produtos acabados.
- **MovimentoFinanceiro** — lançamentos financeiros originados de compras, produção, vendas e ajustes.

### Relacionamentos

De forma conceitual, as entidades interagem assim:

- **Compra de Concreto** vincula-se a **Fornecedor** e alimenta o saldo consumido pela **Produção**.
- **Produção** vincula-se a **Funcionário**, **Produto** e **Compra de Concreto**, gera **MovimentoEstoque** (entrada) e **MovimentoFinanceiro** (custo).
- **Venda** vincula-se a **Cliente** e possui um ou mais **ItemVenda** associados a **Produto**.
- Cada **ItemVenda** motiva **MovimentoEstoque** (saída) e a **Venda** gera **MovimentoFinanceiro** (receita).
- **MovimentoEstoque** e **MovimentoFinanceiro** consolidam, respectivamente, a visão física e financeira dos processos.

### Integridade dos Dados

O sistema adota:

- Soft Delete
- Integridade referencial
- Transações centralizadas
- Consistência entre Estoque, Produção e Financeiro

### Evolução do Banco

Novas entidades deverão seguir o padrão arquitetural adotado pelo projeto (Model → Repository → Service → API), preservando desacoplamento, consistência e rastreabilidade das informações.

## Regras de Negócio

Índice das regras de negócio.

## APIs

Organização das APIs disponíveis.

### Objetivo das APIs

Todas as APIs do SIGPREM seguem arquitetura REST e atuam apenas como camada de comunicação entre o cliente e os Services, sem concentrar regras de negócio.

### Padrão de Funcionamento

Fluxo padrão das APIs:

```text
Cliente
↓
API
↓
Service
↓
Repository
↓
Banco de Dados
↓
Repository
↓
Service
↓
API
↓
Cliente
```

### Responsabilidades da API

As APIs são responsáveis apenas por:

- autenticação;
- validação de parâmetros;
- chamada dos Services;
- retorno das respostas;
- códigos HTTP.

### Responsabilidades dos Services

Toda regra de negócio permanece exclusivamente na camada Service. A API apenas delega a execução e traduz exceções de domínio em respostas HTTP quando necessário.

### Organização dos Endpoints

Grupos de endpoints atualmente existentes:

- **Autenticação** — login e obtenção de token de acesso.
- **Clientes** — CRUD do cadastro de clientes.
- **Fornecedores** — CRUD do cadastro de fornecedores.
- **Produtos** — CRUD do cadastro de produtos.
- **Compras** — CRUD de compras de concreto.
- **Produção** — CRUD de produção e relatório por período.
- **Vendas** — CRUD de vendas e relatório por período.
- **Itens da Venda** — CRUD dos itens associados às vendas.
- **Estoque** — CRUD de movimentos de estoque.
- **Financeiro** — CRUD de movimentos financeiros e fluxo de caixa (geral e por período).
- **Dashboard** — indicadores gerenciais consolidados.

### Princípios adotados

As APIs seguem:

- baixo acoplamento;
- alta coesão;
- reutilização de regras;
- ausência de acesso direto ao banco;
- padronização das respostas.

## Dashboard

Visão geral dos indicadores.

### Objetivo do Dashboard

O Dashboard centraliza os principais indicadores gerenciais do sistema, fornecendo uma visão consolidada da operação financeira, comercial, produtiva e de estoque.

### Arquitetura

O Dashboard é composto exclusivamente por chamadas aos Services existentes, sem consultas diretas ao banco de dados.

Fluxo:

```text
Dashboard API
↓
DashboardService
↓
Services Especializados
↓
Repositories
↓
Banco de Dados
```

### Blocos do Dashboard

Blocos atualmente existentes:

- **Fluxo Financeiro** — consolida entradas, saídas, saldo, quantidade de lançamentos e totais por tipo de movimento financeiro.
- **Comercial** — apresenta quantidade de vendas, valor total, ticket médio, maior e menor venda.
- **Produção** — resume quantidade de produções, volume produzido, custo total e custo médio de produção.
- **Estoque** — indica movimentos, totais de entradas e saídas, saldo total e produtos movimentados.
- **Executivo** — deriva indicadores estratégicos (faturamento, custo, lucro, margem, clientes atendidos e produtos movimentados) a partir dos demais blocos.

### Princípios Arquiteturais

O Dashboard segue:

- reutilização de Services;
- ausência de consultas SQL próprias;
- ausência de regras duplicadas;
- consolidação de indicadores;
- baixo acoplamento.

### Evolução

Novos indicadores deverão reutilizar Services existentes sempre que possível, preservando a arquitetura do projeto e evitando duplicação de regras de negócio.

## Relatórios

Estrutura dos relatórios existentes e futuros.

## Segurança

Autenticação, autorização e boas práticas.

## Convenções de Desenvolvimento

Padrões adotados no projeto.

## Estratégia de Versionamento

Padrão de commits e evolução.

## Roadmap

Planejamento das próximas versões.

## Histórico de Evolução

Resumo da evolução do sistema.

## Deploy

Estrutura prevista para implantação.

## Backup

Estratégia de backup e recuperação.

## Testes

Organização futura dos testes automatizados.

## Licenciamento

Informações sobre distribuição e uso.

## Próximas Versões

Resumo dos módulos planejados.
