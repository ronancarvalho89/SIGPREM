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
