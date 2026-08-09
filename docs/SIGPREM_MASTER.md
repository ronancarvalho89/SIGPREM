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

## Dashboard

Visão geral dos indicadores.

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
