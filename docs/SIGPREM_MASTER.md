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

Módulos existentes no backend:

- Autenticação / Usuários
- Clientes
- Fornecedores
- Produtos
- Funcionários
- Compras de Concreto
- Produção
- Vendas / Itens da Venda
- Estoque
- Financeiro
- Dashboard
- Relatórios
- Auditoria
- Inventário

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

### Fluxo de Inventário

O SIGPREM possui fluxo de inventário físico com:

- criação de inventário;
- status aberto/concluído;
- associação de produtos;
- carregamento do saldo do estoque;
- registro da quantidade física;
- cálculo da diferença;
- conclusão;
- geração de ajustes de estoque;
- integração com Auditoria;
- bloqueio de alterações após conclusão.

Fluxo conceitual:

```text
Criar Inventário (status = aberto)
↓
Adicionar Item
↓
Carregar Saldo do Estoque (quantidade_sistema)
↓
Registrar Contagem Física
↓
Calcular Diferença (física − sistema)
↓
Concluir Inventário
↓
Gerar Ajuste de Estoque (ENTRADA / SAÍDA / nenhum se zero)
↓
Status = concluido
↓
Registrar Auditoria
↓
Bloquear novas alterações
```

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
- **Inventario** — cabeçalho do inventário físico (`status`: `aberto` | `concluido`), vinculado ao usuário responsável.
- **ItemInventario** — itens do inventário, com quantidades de sistema e física, diferença e vínculo a produto.
- **Auditoria** — trilha de operações relevantes registradas pelos Services.

### Relacionamentos

De forma conceitual, as entidades interagem assim:

- **Compra de Concreto** vincula-se a **Fornecedor** e alimenta o saldo consumido pela **Produção**.
- **Produção** vincula-se a **Funcionário**, **Produto** e **Compra de Concreto**, gera **MovimentoEstoque** (entrada) e **MovimentoFinanceiro** (custo).
- **Venda** vincula-se a **Cliente** e possui um ou mais **ItemVenda** associados a **Produto**.
- Cada **ItemVenda** motiva **MovimentoEstoque** (saída) e a **Venda** gera **MovimentoFinanceiro** (receita).
- **Inventario** vincula-se a **Usuário** e possui um ou mais **ItemInventario** associados a **Produto**.
- Na conclusão do inventário, diferenças diferentes de zero geram **MovimentoEstoque** (ENTRADA ou SAÍDA).
- **MovimentoEstoque** e **MovimentoFinanceiro** consolidam, respectivamente, a visão física e financeira dos processos.

### Integridade dos Dados

O sistema adota:

- Soft Delete
- Integridade referencial
- Transações centralizadas
- Consistência entre Estoque, Produção, Financeiro e Inventário

### Evolução do Banco

Novas entidades deverão seguir o padrão arquitetural adotado pelo projeto (Model → Repository → Service → API), preservando desacoplamento, consistência e rastreabilidade das informações.

## Regras de Negócio

Índice das regras de negócio.

### Compras

Toda compra de concreto gera automaticamente um Movimento Financeiro correspondente, registrando o impacto financeiro da aquisição.

### Produção

Toda produção:

- consome compra de concreto;
- calcula automaticamente o custo da mão de obra;
- gera entrada no estoque;
- gera movimento financeiro de custo;
- ocorre em transação única.

### Vendas

Toda venda:

- grava o cabeçalho;
- grava os itens;
- calcula automaticamente os valores;
- valida saldo em estoque;
- gera saída de estoque;
- gera movimento financeiro;
- ocorre em transação única.

### Estoque

As entradas e saídas são originadas pelos processos do sistema (produção, venda e conclusão de inventário), evitando movimentações inconsistentes ou desconectadas da operação.

### Inventário

O inventário físico segue as regras:

- novo inventário inicia com status `aberto`;
- a associação de produto carrega `quantidade_sistema` a partir do saldo atual do estoque;
- a contagem física registra `quantidade_fisica` e calcula `diferenca = quantidade_fisica - quantidade_sistema`;
- a conclusão só é permitida para inventário aberto;
- diferença positiva gera movimento de **ENTRADA**;
- diferença negativa gera movimento de **SAÍDA**;
- diferença zero não gera movimento;
- após `status = concluido`, não é permitido adicionar item, alterar contagem/diferença nem concluir novamente;
- operações relevantes registram auditoria (`modulo = inventario`).

### Financeiro

Os lançamentos financeiros são gerados automaticamente pelos módulos integrados (compra, produção e venda), preservando consistência entre operação e financeiro.

### Dashboard

Todos os indicadores são derivados dos Services existentes, sem lógica própria de cálculo operacional ou consultas diretas ao banco de dados.

### Princípios Gerais

O sistema adota:

- transações atômicas;
- rollback em caso de erro;
- centralização das regras de negócio;
- reutilização de Services;
- integridade entre módulos.

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
- **Auditoria** — consulta autenticada da trilha (`GET /auditoria`).
- **Inventários** — CRUD do cabeçalho e conclusão do inventário.
- **Itens de Inventário** — associação de produtos, contagem física e consulta de itens.

#### Inventários

Endpoints implementados:

- `GET /inventarios` — lista inventários ativos (filtro opcional `status`).
- `GET /inventarios/{inventario_id}` — consulta por id.
- `POST /inventarios` — cria inventário (`status` inicial `aberto`).
- `PUT /inventarios/{inventario_id}` — atualiza campos do inventário aberto.
- `DELETE /inventarios/{inventario_id}` — soft delete (`ativo = False`).
- `POST /inventario/{inventario_id}/concluir` — conclui o inventário e gera ajustes de estoque.

#### Itens de Inventário

Endpoints implementados:

- `GET /inventario/{inventario_id}/itens` — lista itens do inventário.
- `POST /inventario/{inventario_id}/itens` — adiciona item via `InventarioService.adicionar_item` (saldo automático).
- `GET /inventario/item/{item_id}` — consulta item por id.
- `PUT /inventario/item/{item_id}` — atualiza item (inventário aberto).
- `DELETE /inventario/item/{item_id}` — soft delete do item (inventário aberto).
- `POST /inventario/item/{item_id}/contagem` — registra quantidade física e calcula a diferença.

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

### Objetivo da Segurança

A segurança do sistema busca garantir integridade, confidencialidade e rastreabilidade das informações operacionais e gerenciais do SIGPREM.

### Autenticação

Todas as APIs protegidas exigem autenticação antes da execução das operações, assegurando que apenas usuários válidos acessem o sistema.

### Autorização

O projeto está preparado para evolução futura com perfis de acesso e controle de permissões, ampliando a granularidade da segurança por funcionalidade.

### Integridade dos Dados

O sistema utiliza:

- transações atômicas;
- rollback em caso de erro;
- integridade referencial;
- sincronização entre módulos.

### Boas Práticas

O projeto adota:

- separação de responsabilidades;
- centralização das regras de negócio;
- ausência de acesso direto ao banco pelas APIs;
- reutilização de Services;
- Soft Delete quando aplicável.

### Auditoria

O SIGPREM mantém uma trilha de auditoria para registrar operações relevantes do sistema, permitindo rastreabilidade das ações executadas nos módulos de negócio.

A finalidade da auditoria é preservar o histórico operacional, apoiar investigações e reforçar a segurança da informação, sem interferir nas regras de negócio dos módulos integrados.

O registro das operações relevantes é realizado pelos Services internos, por meio do `AuditoriaService.registrar(...)`. A API pública de Auditoria é exclusivamente de consulta e não permite criação, alteração ou exclusão de registros.

Quando o usuário estiver disponível no contexto da operação, o registro identifica o responsável por meio do campo `usuario_id`.

Quando a operação ocorrer fora de um contexto de usuário autenticado, o registro poderá ser gerado sem `usuario_id`, preservando a trilha mesmo sem identificação individual.

A consulta autenticada (`GET /auditoria`) permite filtrar a trilha por:

- período (`data_inicial` e `data_final`);
- usuário (`usuario_id`);
- módulo;
- ação;
- entidade;
- identificador da entidade (`entidade_id`).

Os filtros são opcionais e podem ser combinados com a paginação padrão do projeto.

O histórico de auditoria é preservado: não há exclusão física pela API. Quando aplicável, a inativação lógica (Soft Delete) mantém o registro no banco, sem remoção definitiva.

O módulo Inventário integra-se à Auditoria nas operações relevantes (criação, adição de item, conclusão e ajustes de estoque gerados na conclusão), com `modulo = inventario`.

### Evolução

Futuras versões deverão incorporar:

- perfis de usuários;
- políticas de acesso;
- monitoramento de segurança;
- expansão da cobertura de auditoria para novos módulos.

## Convenções de Desenvolvimento

Padrões adotados no projeto.

### Organização das Camadas

Responsabilidades oficiais:

- **API** — comunicação HTTP, autenticação, validação de parâmetros e delegação ao Service.
- **Service** — regras de negócio, orquestração e controle transacional.
- **Repository** — acesso exclusivo a dados, sem regras de negócio.
- **Model** — representação das entidades e mapeamento com o banco.
- **Schema** — contratos de entrada e saída da API.

### Criação de Novas Funcionalidades

Novas funcionalidades deverão respeitar a arquitetura existente, evitando lógica duplicada e mantendo baixo acoplamento entre as camadas e os módulos.

### Convenções de Código

O projeto adota:

- nomenclatura consistente;
- responsabilidade única por classe;
- reutilização de Services;
- métodos pequenos e coesos;
- separação entre regras de negócio e acesso a dados.

### Convenções de Banco

Novas entidades deverão seguir o padrão arquitetural já estabelecido (Model → Repository → Service → API), preservando integridade e consistência dos dados.

### Convenções de APIs

Novos endpoints deverão:

- reutilizar Services;
- não conter regras de negócio;
- manter padronização REST;
- validar entradas antes da chamada ao Service.

### Convenções de Versionamento

O projeto utiliza commits pequenos, incrementais e rastreáveis, preservando histórico claro de evolução.

### Objetivo das Convenções

Essas convenções visam facilitar manutenção, escalabilidade, testes e evolução contínua do sistema.

## Estratégia de Versionamento

Padrão de commits e evolução.

## Roadmap

Planejamento das próximas versões.

### Versão 1.0

Funcionalidades concluídas:

- Autenticação
- Clientes
- Fornecedores
- Produtos
- Compras de Concreto
- Produção
- Vendas
- Itens da Venda
- Controle de Estoque
- Controle Financeiro
- Dashboard Gerencial
- Relatórios por Período
- Documentação Técnica Inicial
- Inventário de Estoque (com ajustes na conclusão)
- Auditoria (consulta e integração nos Services)
- Testes automatizados de Auditoria e Inventário

### Versão 1.1

Funcionalidades planejadas:

- Relatórios em PDF
- Exportação para Excel
- Melhorias no Dashboard
- Filtros avançados
- Indicadores adicionais

### Versão 1.2

Funcionalidades planejadas:

- Cancelamentos
- Estornos
- Histórico de Alterações

### Versão 2.0

Evolução do produto:

- Controle de Usuários e Perfis
- Logs
- Configurações Gerais
- Backup
- Docker
- Deploy em Produção
- Expansão da cobertura de testes automatizados
- CI/CD
- Integração com novos módulos

### Objetivo do Roadmap

O Roadmap orienta a evolução do SIGPREM de forma organizada, incremental e compatível com a arquitetura existente.

## Histórico de Evolução

Resumo da evolução do sistema.

### Início do Projeto

O projeto foi concebido para atender o gerenciamento completo de uma fábrica de pré-moldados, com foco na integração entre os setores operacional e administrativo.

### Evolução da Arquitetura

Foi adotada a arquitetura em camadas:

- API
- Service
- Repository
- Model

Essa organização trouxe separação de responsabilidades, facilidade de manutenção, baixo acoplamento e maior reutilização das regras de negócio.

### Evolução Funcional

Foram implantados os principais módulos:

- Cadastros
- Compras
- Produção
- Estoque
- Financeiro
- Vendas
- Dashboard
- Relatórios
- Auditoria
- Inventário

### Consolidação da Arquitetura

A integração entre Produção, Estoque, Financeiro, Vendas e Inventário passou a ocorrer automaticamente por meio das regras de negócio centralizadas nos Services, com execução em transação única e rollback em caso de erro.

### Documentação Técnica

Após a consolidação do backend, iniciou-se a documentação oficial da arquitetura, banco de dados, fluxos, APIs, dashboard, regras de negócio e roadmap. O Inventário e a Auditoria passaram a constar como módulos implementados.

### Próxima Etapa

As próximas evoluções estarão concentradas em funcionalidades Enterprise, expansão da cobertura de testes, deploy, segurança e novos módulos.

## Deploy

Estrutura prevista para implantação.

## Backup

Estratégia de backup e recuperação.

## Testes

Organização dos testes automatizados.

### Objetivo

Os testes têm como finalidade garantir estabilidade, confiabilidade e evolução segura do sistema.

### Infraestrutura

A suíte utiliza `pytest` com `tests/conftest.py` (sessão SQLite em memória e fixtures compartilhadas).

### Cobertura atual

Suíte validada com **38 testes passando**:

- **Auditoria** (`tests/test_auditoria.py`) — 16 testes;
- **Inventário** (`tests/test_inventario.py`) — 22 testes.

O módulo Inventário possui testes automatizados cobrindo CRUD, status, adição de item com saldo, contagem/diferença, conclusão com ajustes de estoque, bloqueio após conclusão, autenticação da API e regressão da Auditoria.

O fluxo completo do Inventário foi validado:

criar → adicionar item → carregar saldo → contagem → diferença → concluir → ajuste de estoque → auditoria → bloqueio.

### Testes Unitários

Validam individualmente, nos módulos cobertos:

- Services;
- regras de negócio;
- cálculos;
- validações.

### Testes de Integração

Validam, nos módulos cobertos:

- integração entre APIs, Services e Repositories;
- persistência dos dados;
- integrações Inventário ↔ Estoque e Inventário ↔ Auditoria.

### Testes Funcionais

Cobertura funcional atual inclui:

- Auditoria;
- Inventário (fluxo completo).

Demais fluxos do ERP (Compras, Produção, Vendas, Estoque, Financeiro, Dashboard) permanecem como expansão prevista da suíte.

### Regressão

Novas funcionalidades não deverão comprometer comportamentos já implementados. Alterações no Inventário devem manter a suíte de Auditoria verde.

### Evolução

Futuras versões deverão ampliar a cobertura automatizada e incorporar os testes ao pipeline de integração contínua.

## Licenciamento

Informações sobre distribuição e uso.

## Próximas Versões

Resumo das evoluções planejadas (ver Roadmap). Inventário e Auditoria já estão implementados.
