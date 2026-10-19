# SDD — Software Design Description
## Sistema de Monitoramento de Planta Industrial (Supervisório Leve)

| Campo               | Valor                                                   |
|---------------------|---------------------------------------------------------|
| **Projeto**         | PlantaView — Supervisório Leve de Planta Industrial     |
| **Disciplina**      | Desenvolvimento de Aplicações Orientadas a Serviços     |
| **Professor**       | Luis Paulo da Silva Carvalho                            |
| **Instituição**     | IFBA — Pós-Graduação em Desenvolvimento Web             |
| **Data de Entrega** | 20/09/2026                                              |
| **Versão**          | 1.0                                                     |
| **Norma Base**      | IEEE 1016 (Software Design Description) — adaptada      |

---

## Sumário

1. [Introdução](#1-introdução)
2. [Referências](#2-referências)
3. [Glossário](#3-glossário)
4. [Visão Geral da Arquitetura](#4-visão-geral-da-arquitetura)
5. [Modelo de Domínio (Mini-Mundo)](#5-modelo-de-domínio-mini-mundo)
6. [Viewpoint de Decomposição](#6-viewpoint-de-decomposição)
7. [Viewpoint de Dados](#7-viewpoint-de-dados)
8. [Viewpoint de Interface (API REST)](#8-viewpoint-de-interface-api-rest)
9. [Viewpoint MCP (Model Context Protocol)](#9-viewpoint-mcp-model-context-protocol)
10. [Viewpoint de Implantação (Docker)](#10-viewpoint-de-implantação-docker)
11. [Cliente Web (Dashboard)](#11-cliente-web-dashboard)
12. [Chat com IA (Gemini)](#12-chat-com-ia-gemini)
13. [Requisitos Não-Funcionais & Resiliência](#13-requisitos-não-funcionais--resiliência)
14. [Seed de Dados](#14-seed-de-dados)
15. [Estrutura de Diretórios do Projeto](#15-estrutura-de-diretórios-do-projeto)
16. [Plano de Verificação](#16-plano-de-verificação)
17. [Rastreabilidade de Requisitos](#17-rastreabilidade-de-requisitos)

---

## 1. Introdução

### 1.1 Propósito

Este documento descreve o design de software do sistema **PlantaView**, um supervisório leve para monitoramento de uma planta industrial de pequeno porte. O sistema acompanha leituras de sensores, trata alarmes de limite excedido e gerencia ordens de manutenção de equipamentos instrumentados (bombas, compressores, motores e caldeiras).

### 1.2 Escopo

O PlantaView é composto por **três microsserviços web RESTful** independentes, cada um encapsulado em seu próprio contêiner Docker com banco de dados PostgreSQL dedicado:

| Serviço         | Responsabilidade                                                       |
|-----------------|------------------------------------------------------------------------|
| **Sensores**    | Leituras de temperatura, pressão e vibração por equipamento e período  |
| **Alarmes**     | Eventos de limite excedido, com severidade e status                    |
| **Manutenção**  | Ordens de serviço abertas e histórico por equipamento                  |

Complementam a solução:
- Um **cliente web** (dashboard/painel) que consome os três serviços de forma independente e continua funcionando caso algum serviço fique indisponível;
- Três **servidores MCP** (Model Context Protocol) que expõem as ferramentas de cada serviço para consumo por uma IA;
- Um **chat conversacional** integrado ao modelo **Google Gemini** que utiliza as ferramentas MCP para responder perguntas operacionais.

### 1.3 Stakeholders

| Papel               | Descrição                                                          |
|----------------------|--------------------------------------------------------------------|
| Operador de Planta   | Acompanha leituras, trata alarmes e solicita manutenção            |
| Engenheiro de Manutenção | Gerencia ordens de serviço e histórico de intervenções         |
| Supervisor           | Consulta indicadores agregados e interage com o chat IA            |

---

## 2. Referências

| Documento                              | Descrição                                              |
|----------------------------------------|--------------------------------------------------------|
| IEEE 1016-2009                         | Standard for Software Design Descriptions              |
| IFBA-SOA-Avaliacao-v3.0.pdf            | Especificação da avaliação da disciplina               |
| Projeto KKKBoom (referência do prof.)  | Arquitetura de referência com Flask + Postgres + MCP   |
| Model Context Protocol (MCP) Spec      | Protocolo de comunicação IA ↔ ferramentas              |
| FastMCP 4.x                            | Framework Python para servidores MCP                   |
| Google GenAI SDK                       | SDK Python para integração com Gemini                  |

---

## 3. Glossário

| Termo        | Definição                                                                                |
|--------------|------------------------------------------------------------------------------------------|
| **MCP**      | Model Context Protocol — protocolo aberto para expor ferramentas para modelos de IA      |
| **OS**       | Ordem de Serviço — registro de atividade de manutenção                                   |
| **Tag**      | Identificador único de um ponto de medição (sensor)                                      |
| **Setpoint** | Valor-limite configurado que, ao ser ultrapassado, gera um alarme                        |
| **SCADA**    | Supervisory Control And Data Acquisition — sistema supervisório clássico                 |
| **SDD**      | Software Design Description — documento de design de software                            |
| **REST**     | Representational State Transfer — estilo arquitetural de APIs                            |

---

## 4. Visão Geral da Arquitetura

### 4.1 Estilo Arquitetural

O sistema adota a **arquitetura de microsserviços RESTful** com isolamento total por contêiner Docker. Cada serviço possui seu próprio banco PostgreSQL, seguindo o princípio de **database-per-service**. A comunicação entre componentes ocorre exclusivamente via HTTP/REST sobre uma rede Docker compartilhada.

### 4.2 Diagrama de Contexto (C4 — Nível 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUÁRIOS                                     │
│   ┌──────────────┐                    ┌──────────────────────┐      │
│   │  Operador /  │                    │  Supervisor          │      │
│   │  Engenheiro  │                    │  (Chat IA)           │      │
│   └──────┬───────┘                    └──────────┬───────────┘      │
│          │ HTTP                                  │ stdin/stdout     │
└──────────┼──────────────────────────────────────┼──────────────────┘
           │                                      │
           ▼                                      ▼
┌──────────────────┐                  ┌──────────────────────────┐
│  Dashboard Web   │                  │  Chat Gemini (Python)    │
│  (HTML/JS/CSS)   │                  │  chat_google.py          │
└──────┬───┬───┬───┘                  └───┬────────┬────────┬────┘
       │   │   │                          │        │        │
       │   │   │ HTTP (REST)              │        │        │ MCP/HTTP
       ▼   ▼   ▼                          ▼        ▼        ▼
┌──────┐┌──────┐┌──────────┐    ┌────────┐┌───────┐┌───────────┐
│Senso-││Alar- ││Manuten-  │    │Sens-MCP││Ala-MCP││Manut-MCP  │
│res   ││mes   ││ção       │    │:8001   ││:8002  ││:8003      │
│:7001 ││:7002 ││:7003     │    └───┬────┘└───┬───┘└─────┬─────┘
└──┬───┘└──┬───┘└────┬─────┘        │         │          │
   │       │         │              │ HTTP     │          │ HTTP
   ▼       ▼         ▼              ▼         ▼          ▼
┌──────┐┌──────┐┌──────────┐    ┌──────┐┌──────┐┌──────────┐
│PG    ││PG    ││PG        │    │Senso-││Alar- ││Manuten-  │
│Senso-││Alar- ││Manuten-  │    │res   ││mes   ││ção       │
│res   ││mes   ││ção       │    │:7001 ││:7002 ││:7003     │
│:7004 ││:7005 ││:7006     │    └──────┘└──────┘└──────────┘
└──────┘└──────┘└──────────┘
```

### 4.3 Fluxo de Comunicação

```
Dashboard (browser)  ──HTTP/REST──►  Serviço Flask  ──SQL──►  PostgreSQL
                                          ▲
Chat (terminal)  ──Gemini API──►  Google  │
                                  Gemini  │
Chat (terminal)  ──MCP/HTTP──►  Servidor  │ HTTP
                                  MCP  ───┘
```

### 4.4 Mapa de Portas

| Componente            | Porta Host | Porta Contêiner | Protocolo      |
|-----------------------|------------|-----------------|----------------|
| Serviço Sensores      | 7001       | 5000            | HTTP/REST      |
| Serviço Alarmes       | 7002       | 5000            | HTTP/REST      |
| Serviço Manutenção    | 7003       | 5000            | HTTP/REST      |
| PostgreSQL Sensores   | 7004       | 5432            | PostgreSQL     |
| PostgreSQL Alarmes    | 7005       | 5432            | PostgreSQL     |
| PostgreSQL Manutenção | 7006       | 5432            | PostgreSQL     |
| MCP Sensores          | 8001       | 8000            | HTTP (MCP SSE) |
| MCP Alarmes           | 8002       | 8000            | HTTP (MCP SSE) |
| MCP Manutenção        | 8003       | 8000            | HTTP (MCP SSE) |

---

## 5. Modelo de Domínio (Mini-Mundo)

### 5.1 Descrição do Mini-Mundo

Uma **fábrica de pequeno porte** opera com os seguintes equipamentos instrumentados:

| ID  | Equipamento     | Tipo        | Localização    |
|-----|-----------------|-------------|----------------|
| 1   | Bomba 1         | bomba       | Sala de Bombas |
| 2   | Bomba 2         | bomba       | Sala de Bombas |
| 3   | Compressor 1    | compressor  | Utilidades     |
| 4   | Compressor 2    | compressor  | Utilidades     |
| 5   | Compressor 3    | compressor  | Utilidades     |
| 6   | Motor 1         | motor       | Linha de Produção |
| 7   | Motor 2         | motor       | Linha de Produção |
| 8   | Caldeira 1      | caldeira    | Casa de Caldeiras |

Cada equipamento possui **sensores** que medem:
- **Temperatura** (°C)
- **Pressão** (bar)
- **Vibração** (mm/s)

Os sensores enviam leituras periódicas. Quando um valor excede o **setpoint** configurado, um **alarme** é gerado automaticamente. Equipamentos que apresentam problemas recorrentes ou falhas geram **ordens de serviço** de manutenção.

### 5.2 Diagrama Entidade-Relacionamento Conceitual

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│ EQUIPAMENTO  │1    N │   SENSOR     │1    N │    LEITURA       │
│──────────────│───────│──────────────│───────│──────────────────│
│ id           │       │ id           │       │ id               │
│ nome         │       │ equipamento_ │       │ sensor_id        │
│ tipo         │       │   id         │       │ valor            │
│ localizacao  │       │ grandeza     │       │ unidade          │
│              │       │ setpoint_min │       │ registrado_em    │
│              │       │ setpoint_max │       │                  │
└──────┬───────┘       │ unidade      │       └──────────────────┘
       │               └──────────────┘
       │
       │1    N ┌──────────────────┐
       │───────│    ALARME        │
       │       │──────────────────│
       │       │ id               │
       │       │ equipamento_id   │
       │       │ sensor_id        │
       │       │ grandeza         │
       │       │ valor_lido       │
       │       │ setpoint         │
       │       │ severidade       │
       │       │ status           │
       │       │ criado_em        │
       │       │ reconhecido_em   │
       │       │ encerrado_em     │
       │       └──────────────────┘
       │
       │1    N ┌──────────────────────┐
       └───────│  ORDEM_SERVICO       │
               │──────────────────────│
               │ id                   │
               │ equipamento_id       │
               │ tipo_manutencao      │
               │ descricao            │
               │ status               │
               │ prioridade           │
               │ criada_em            │
               │ concluida_em         │
               │ tecnico_responsavel  │
               │ observacoes          │
               └──────────────────────┘
```

---

## 6. Viewpoint de Decomposição

### 6.1 Princípio de Modularização

Cada serviço realiza **somente uma coisa** (conforme requisito 5 da avaliação):

| Serviço      | Responsabilidade Única                                  |
|--------------|---------------------------------------------------------|
| Sensores     | Persistir e consultar leituras de sensores              |
| Alarmes      | Registrar, consultar e gerenciar alarmes de limite      |
| Manutenção   | Gerenciar ordens de serviço e histórico de manutenção   |

### 6.2 Componentes Internos de Cada Serviço

Cada microsserviço Flask segue esta estrutura interna:

```
servico.py
├── Configuração (Flask, CORS, constantes de BD)
├── Função de conexão com BD (get_conexao_com_bd)
├── Rota de informação (GET /)
├── Rotas de negócio (GET /recurso, GET /recurso/<filtro>)
└── Entrypoint (__main__ → servico.run)
```

### 6.3 Stack Tecnológica

| Camada              | Tecnologia                         | Versão     |
|---------------------|------------------------------------|------------|
| Linguagem           | Python                             | 3.12+      |
| Framework Web       | Flask                              | 3.1.x      |
| Driver PostgreSQL   | psycopg (binary)                   | 3.3.x      |
| CORS                | flask-cors                         | latest     |
| Servidor MCP        | fastmcp                            | 4.0.x      |
| SDK Google AI       | google-genai                       | 2.21.x     |
| Contêinerização     | Docker + Docker Compose            | latest     |
| Banco de Dados      | PostgreSQL                         | latest     |
| Dashboard           | HTML5 + JavaScript + Chart.js      | vanilla    |

---

## 7. Viewpoint de Dados

### 7.1 Banco: `plantaview_sensores` (porta host 7004)

```sql
-- Schema: plantaview

CREATE SCHEMA IF NOT EXISTS plantaview;

-- Tabela de equipamentos (replicada em cada banco para referência)
CREATE TABLE plantaview.equipamentos (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    tipo            VARCHAR(50)  NOT NULL,  -- bomba, compressor, motor, caldeira
    localizacao     VARCHAR(100) NOT NULL
);

-- Tabela de sensores
CREATE TABLE plantaview.sensores (
    id              SERIAL PRIMARY KEY,
    equipamento_id  INTEGER NOT NULL REFERENCES plantaview.equipamentos(id),
    grandeza        VARCHAR(20) NOT NULL,   -- temperatura, pressao, vibracao
    unidade         VARCHAR(10) NOT NULL,   -- °C, bar, mm/s
    setpoint_min    NUMERIC(10,2),
    setpoint_max    NUMERIC(10,2)
);

-- Tabela de leituras
CREATE TABLE plantaview.leituras (
    id              SERIAL PRIMARY KEY,
    sensor_id       INTEGER NOT NULL REFERENCES plantaview.sensores(id),
    valor           NUMERIC(10,2) NOT NULL,
    unidade         VARCHAR(10) NOT NULL,
    registrado_em   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- View: leituras com informações do equipamento e sensor
CREATE VIEW plantaview.vw_leituras_detalhadas AS
SELECT
    l.id            AS leitura_id,
    e.id            AS equipamento_id,
    e.nome          AS equipamento_nome,
    e.tipo          AS equipamento_tipo,
    s.grandeza,
    l.valor,
    l.unidade,
    s.setpoint_min,
    s.setpoint_max,
    l.registrado_em
FROM plantaview.leituras l
JOIN plantaview.sensores s ON l.sensor_id = s.id
JOIN plantaview.equipamentos e ON s.equipamento_id = e.id;

-- View: última leitura por sensor
CREATE VIEW plantaview.vw_ultima_leitura AS
SELECT DISTINCT ON (s.id)
    s.id            AS sensor_id,
    e.id            AS equipamento_id,
    e.nome          AS equipamento_nome,
    s.grandeza,
    l.valor,
    l.unidade,
    s.setpoint_min,
    s.setpoint_max,
    l.registrado_em
FROM plantaview.sensores s
JOIN plantaview.leituras l ON l.sensor_id = s.id
JOIN plantaview.equipamentos e ON s.equipamento_id = e.id
ORDER BY s.id, l.registrado_em DESC;

-- Índices para performance
CREATE INDEX idx_leituras_sensor_data ON plantaview.leituras (sensor_id, registrado_em DESC);
CREATE INDEX idx_leituras_data ON plantaview.leituras (registrado_em DESC);
```

### 7.2 Banco: `plantaview_alarmes` (porta host 7005)

```sql
CREATE SCHEMA IF NOT EXISTS plantaview;

-- Tabela de equipamentos (referência local)
CREATE TABLE plantaview.equipamentos (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    tipo            VARCHAR(50)  NOT NULL,
    localizacao     VARCHAR(100) NOT NULL
);

-- Tabela de alarmes
CREATE TABLE plantaview.alarmes (
    id              SERIAL PRIMARY KEY,
    equipamento_id  INTEGER NOT NULL REFERENCES plantaview.equipamentos(id),
    grandeza        VARCHAR(20) NOT NULL,   -- temperatura, pressao, vibracao
    valor_lido      NUMERIC(10,2) NOT NULL,
    setpoint        NUMERIC(10,2) NOT NULL,
    severidade      VARCHAR(20) NOT NULL,   -- baixa, media, alta, critica
    status          VARCHAR(20) NOT NULL DEFAULT 'ativo',  -- ativo, reconhecido, encerrado
    criado_em       TIMESTAMP NOT NULL DEFAULT NOW(),
    reconhecido_em  TIMESTAMP,
    encerrado_em    TIMESTAMP
);

-- View: resumo de alarmes com equipamento
CREATE VIEW plantaview.vw_alarmes_detalhados AS
SELECT
    a.id            AS alarme_id,
    e.id            AS equipamento_id,
    e.nome          AS equipamento_nome,
    e.tipo          AS equipamento_tipo,
    a.grandeza,
    a.valor_lido,
    a.setpoint,
    a.severidade,
    a.status,
    a.criado_em,
    a.reconhecido_em,
    a.encerrado_em
FROM plantaview.alarmes a
JOIN plantaview.equipamentos e ON a.equipamento_id = e.id;

-- View: contagem de alarmes por equipamento
CREATE VIEW plantaview.vw_alarmes_por_equipamento AS
SELECT
    e.id            AS equipamento_id,
    e.nome          AS equipamento_nome,
    a.severidade,
    COUNT(*)        AS total_alarmes
FROM plantaview.alarmes a
JOIN plantaview.equipamentos e ON a.equipamento_id = e.id
GROUP BY e.id, e.nome, a.severidade
ORDER BY total_alarmes DESC;

-- Índices
CREATE INDEX idx_alarmes_equip ON plantaview.alarmes (equipamento_id);
CREATE INDEX idx_alarmes_status ON plantaview.alarmes (status);
CREATE INDEX idx_alarmes_severidade ON plantaview.alarmes (severidade);
CREATE INDEX idx_alarmes_criado ON plantaview.alarmes (criado_em DESC);
```

### 7.3 Banco: `plantaview_manutencao` (porta host 7006)

```sql
CREATE SCHEMA IF NOT EXISTS plantaview;

-- Tabela de equipamentos (referência local)
CREATE TABLE plantaview.equipamentos (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    tipo            VARCHAR(50)  NOT NULL,
    localizacao     VARCHAR(100) NOT NULL
);

-- Tabela de ordens de serviço
CREATE TABLE plantaview.ordens_servico (
    id                  SERIAL PRIMARY KEY,
    equipamento_id      INTEGER NOT NULL REFERENCES plantaview.equipamentos(id),
    tipo_manutencao     VARCHAR(30) NOT NULL,   -- preventiva, corretiva, preditiva
    descricao           TEXT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'aberta',  -- aberta, em_andamento, concluida, cancelada
    prioridade          VARCHAR(20) NOT NULL DEFAULT 'normal',  -- baixa, normal, alta, urgente
    criada_em           TIMESTAMP NOT NULL DEFAULT NOW(),
    concluida_em        TIMESTAMP,
    tecnico_responsavel VARCHAR(100),
    observacoes         TEXT
);

-- View: ordens de serviço com equipamento
CREATE VIEW plantaview.vw_ordens_detalhadas AS
SELECT
    os.id               AS ordem_id,
    e.id                AS equipamento_id,
    e.nome              AS equipamento_nome,
    e.tipo              AS equipamento_tipo,
    os.tipo_manutencao,
    os.descricao,
    os.status,
    os.prioridade,
    os.criada_em,
    os.concluida_em,
    os.tecnico_responsavel,
    os.observacoes
FROM plantaview.ordens_servico os
JOIN plantaview.equipamentos e ON os.equipamento_id = e.id;

-- View: resumo por equipamento
CREATE VIEW plantaview.vw_manutencao_por_equipamento AS
SELECT
    e.id                AS equipamento_id,
    e.nome              AS equipamento_nome,
    COUNT(*)            AS total_ordens,
    COUNT(*) FILTER (WHERE os.status = 'aberta')        AS abertas,
    COUNT(*) FILTER (WHERE os.status = 'em_andamento')  AS em_andamento,
    COUNT(*) FILTER (WHERE os.status = 'concluida')     AS concluidas
FROM plantaview.ordens_servico os
JOIN plantaview.equipamentos e ON os.equipamento_id = e.id
GROUP BY e.id, e.nome;

-- Índices
CREATE INDEX idx_os_equip ON plantaview.ordens_servico (equipamento_id);
CREATE INDEX idx_os_status ON plantaview.ordens_servico (status);
CREATE INDEX idx_os_criada ON plantaview.ordens_servico (criada_em DESC);
```

---

## 8. Viewpoint de Interface (API REST)

### 8.1 Serviço Sensores (`:7001`)

| Método | Endpoint                                              | Descrição                                                  |
|--------|-------------------------------------------------------|------------------------------------------------------------|
| GET    | `/`                                                   | Informações do serviço (nome, versão)                      |
| GET    | `/leituras`                                           | Lista todas as leituras (com dados do equipamento/sensor)  |
| GET    | `/leituras/equipamento/<int:id>`                      | Leituras filtradas por equipamento                         |
| GET    | `/leituras/equipamento/<int:id>/grandeza/<string:g>`  | Leituras por equipamento e grandeza (temperatura, etc.)    |
| GET    | `/leituras/periodo/<string:inicio>/<string:fim>`      | Leituras dentro de um período (ISO 8601)                   |
| GET    | `/leituras/ultima`                                    | Última leitura de cada sensor                              |

**Exemplo de resposta** (`GET /leituras/equipamento/2`):
```json
[
    {
        "leitura_id": 145,
        "equipamento_id": 2,
        "equipamento_nome": "Bomba 2",
        "equipamento_tipo": "bomba",
        "grandeza": "temperatura",
        "valor": 78.50,
        "unidade": "°C",
        "setpoint_min": 20.00,
        "setpoint_max": 85.00,
        "registrado_em": "2026-09-19T14:30:00"
    }
]
```

### 8.2 Serviço Alarmes (`:7002`)

| Método | Endpoint                                              | Descrição                                                  |
|--------|-------------------------------------------------------|------------------------------------------------------------|
| GET    | `/`                                                   | Informações do serviço                                     |
| GET    | `/alarmes`                                            | Lista todos os alarmes                                     |
| GET    | `/alarmes/equipamento/<int:id>`                       | Alarmes filtrados por equipamento                          |
| GET    | `/alarmes/status/<string:status>`                     | Alarmes por status (ativo, reconhecido, encerrado)         |
| GET    | `/alarmes/severidade/<string:severidade>`             | Alarmes por severidade (baixa, media, alta, critica)       |
| GET    | `/alarmes/resumo`                                     | Contagem de alarmes por equipamento e severidade           |

**Exemplo de resposta** (`GET /alarmes/severidade/critica`):
```json
[
    {
        "alarme_id": 42,
        "equipamento_id": 8,
        "equipamento_nome": "Caldeira 1",
        "equipamento_tipo": "caldeira",
        "grandeza": "pressao",
        "valor_lido": 12.80,
        "setpoint": 10.00,
        "severidade": "critica",
        "status": "ativo",
        "criado_em": "2026-09-19T16:45:00"
    }
]
```

### 8.3 Serviço Manutenção (`:7003`)

| Método | Endpoint                                              | Descrição                                                  |
|--------|-------------------------------------------------------|------------------------------------------------------------|
| GET    | `/`                                                   | Informações do serviço                                     |
| GET    | `/ordens`                                             | Lista todas as ordens de serviço                           |
| GET    | `/ordens/equipamento/<int:id>`                        | Ordens filtradas por equipamento                           |
| GET    | `/ordens/status/<string:status>`                      | Ordens por status (aberta, em_andamento, concluida)        |
| GET    | `/ordens/resumo`                                      | Resumo de manutenção por equipamento                       |
| GET    | `/ordens/equipamento/<int:id>/historico`              | Histórico completo de manutenção de um equipamento         |

**Exemplo de resposta** (`GET /ordens/equipamento/5`):
```json
[
    {
        "ordem_id": 17,
        "equipamento_id": 5,
        "equipamento_nome": "Compressor 3",
        "equipamento_tipo": "compressor",
        "tipo_manutencao": "corretiva",
        "descricao": "Troca de rolamento com vibração excessiva",
        "status": "aberta",
        "prioridade": "alta",
        "criada_em": "2026-09-18T09:00:00",
        "tecnico_responsavel": "Carlos Silva",
        "observacoes": "Peça em estoque"
    }
]
```

---

## 9. Viewpoint MCP (Model Context Protocol)

### 9.1 Arquitetura MCP

Cada serviço REST possui um **servidor MCP dedicado** que atua como proxy, consumindo as rotas REST via HTTP interno (rede Docker) e expondo ferramentas para a IA.

```
Chat Gemini ──MCP/HTTP──► MCP Server ──HTTP interno──► Flask REST ──SQL──► PostgreSQL
```

### 9.2 Ferramentas MCP — Sensores (`:8001`)

| Ferramenta                       | Descrição                                                        | Parâmetros          |
|----------------------------------|------------------------------------------------------------------|---------------------|
| `leituras_por_equipamento`       | Retorna leituras de sensores de um equipamento                   | `equipamento_id`    |
| `leituras_por_grandeza`          | Retorna leituras de um equipamento filtradas por grandeza         | `equipamento_id`, `grandeza` |
| `ultima_leitura`                 | Retorna a última leitura de cada sensor                          | —                   |

### 9.3 Ferramentas MCP — Alarmes (`:8002`)

| Ferramenta                       | Descrição                                                        | Parâmetros          |
|----------------------------------|------------------------------------------------------------------|---------------------|
| `alarmes_por_equipamento`        | Retorna alarmes de um equipamento                                | `equipamento_id`    |
| `alarmes_por_severidade`         | Retorna alarmes filtrados por severidade                         | `severidade`        |
| `resumo_alarmes`                 | Retorna contagem de alarmes por equipamento e severidade         | —                   |

### 9.4 Ferramentas MCP — Manutenção (`:8003`)

| Ferramenta                       | Descrição                                                        | Parâmetros          |
|----------------------------------|------------------------------------------------------------------|---------------------|
| `ordens_por_equipamento`         | Retorna ordens de serviço de um equipamento                      | `equipamento_id`    |
| `ordens_por_status`              | Retorna ordens de serviço filtradas por status                   | `status`            |
| `resumo_manutencao`              | Retorna resumo de manutenção por equipamento                     | —                   |

### 9.5 Exemplos de Perguntas para o Chat

| Pergunta do Usuário                                             | Ferramentas Acionadas                               |
|-----------------------------------------------------------------|------------------------------------------------------|
| "Qual equipamento teve mais alarmes críticos essa semana?"      | `alarmes_por_severidade` ou `resumo_alarmes`         |
| "Tem OS aberta pro compressor 3?"                               | `ordens_por_equipamento` (id=5)                      |
| "Qual foi a temperatura máxima da bomba 2 ontem?"               | `leituras_por_grandeza` (id=2, grandeza=temperatura) |
| "Quais alarmes estão ativos agora?"                             | `alarmes_por_severidade` + filtro status             |
| "Resumo de manutenção da caldeira"                              | `ordens_por_equipamento` (id=8)                      |

---

## 10. Viewpoint de Implantação (Docker)

### 10.1 Rede Docker

```bash
docker network create rede-plantaview
```

Todos os contêineres se conectam a esta rede externa compartilhada, permitindo comunicação por hostname.

### 10.2 Docker Compose — Serviços (`servicos/docker-compose.yml`)

```yaml
services:
  sensores:
    build: .
    container_name: sensores
    hostname: sensores
    restart: always
    volumes:
      - ./sensores:/servico
    ports:
      - "7001:5000"
    command: python3 /servico/servico.py
    depends_on:
      - dados-sensores
    networks:
      - rede-plantaview

  alarmes:
    build: .
    container_name: alarmes
    hostname: alarmes
    restart: always
    volumes:
      - ./alarmes:/servico
    ports:
      - "7002:5000"
    command: python3 /servico/servico.py
    depends_on:
      - dados-alarmes
    networks:
      - rede-plantaview

  manutencao:
    build: .
    container_name: manutencao
    hostname: manutencao
    restart: always
    volumes:
      - ./manutencao:/servico
    ports:
      - "7003:5000"
    command: python3 /servico/servico.py
    depends_on:
      - dados-manutencao
    networks:
      - rede-plantaview

  dados-sensores:
    image: postgres:latest
    container_name: dados-sensores
    hostname: dados-sensores
    restart: always
    ports:
      - "7004:5432"
    volumes:
      - ./sensores/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_PASSWORD=admin
      - POSTGRES_USER=admin
      - POSTGRES_DB=plantaview_sensores
      - POSTGRES_HOST_AUTH_METHOD=trust
    networks:
      - rede-plantaview

  dados-alarmes:
    image: postgres:latest
    container_name: dados-alarmes
    hostname: dados-alarmes
    restart: always
    ports:
      - "7005:5432"
    volumes:
      - ./alarmes/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_PASSWORD=admin
      - POSTGRES_USER=admin
      - POSTGRES_DB=plantaview_alarmes
      - POSTGRES_HOST_AUTH_METHOD=trust
    networks:
      - rede-plantaview

  dados-manutencao:
    image: postgres:latest
    container_name: dados-manutencao
    hostname: dados-manutencao
    restart: always
    ports:
      - "7006:5432"
    volumes:
      - ./manutencao/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      - POSTGRES_PASSWORD=admin
      - POSTGRES_USER=admin
      - POSTGRES_DB=plantaview_manutencao
      - POSTGRES_HOST_AUTH_METHOD=trust
    networks:
      - rede-plantaview

networks:
  rede-plantaview:
    external: true
```

### 10.3 Docker Compose — MCP (`mcp/docker-compose.yml`)

```yaml
services:
  sensores-mcp:
    build: .
    container_name: sensores-mcp
    hostname: sensores-mcp
    restart: always
    volumes:
      - ./sensores:/mcp
    command: python3 /mcp/ferramentas.py
    ports:
      - "8001:8000"
    networks:
      - rede-plantaview

  alarmes-mcp:
    build: .
    container_name: alarmes-mcp
    hostname: alarmes-mcp
    restart: always
    volumes:
      - ./alarmes:/mcp
    command: python3 /mcp/ferramentas.py
    ports:
      - "8002:8000"
    networks:
      - rede-plantaview

  manutencao-mcp:
    build: .
    container_name: manutencao-mcp
    hostname: manutencao-mcp
    restart: always
    volumes:
      - ./manutencao:/mcp
    command: python3 /mcp/ferramentas.py
    ports:
      - "8003:8000"
    networks:
      - rede-plantaview

networks:
  rede-plantaview:
    external: true
```

### 10.4 Dockerfile — Serviços (`servicos/Dockerfile`)

```dockerfile
FROM python:latest

RUN pip3 install flask psycopg[binary] flask-cors

RUN mkdir /servico
WORKDIR /servico
```

### 10.5 Dockerfile — MCP (`mcp/Dockerfile`)

```dockerfile
FROM python:latest

RUN pip3 install fastmcp==4.0.0

WORKDIR /mcp
```

---

## 11. Cliente Web (Dashboard)

### 11.1 Visão Geral

O dashboard é um arquivo HTML estático (`dashboard.html`) servido localmente pelo navegador, que consome os três serviços REST de forma **independente**. Utiliza JavaScript vanilla e a biblioteca Chart.js para visualização.

### 11.2 Funcionalidades do Painel

| Seção                   | Dados Consumidos              | Serviço  | Visualização              |
|-------------------------|-------------------------------|----------|---------------------------|
| Cards de resumo         | Totais agregados              | Todos    | Cartões numéricos         |
| Últimas leituras        | Leituras em tempo real        | Sensores | Tabela com indicadores    |
| Gráfico de temperaturas | Leituras de temperatura       | Sensores | Gráfico de barras         |
| Alarmes ativos          | Alarmes com status=ativo      | Alarmes  | Tabela com severidade     |
| Distribuição de alarmes | Contagem por severidade       | Alarmes  | Gráfico de rosca/doughnut |
| Ordens abertas          | OS com status=aberta          | Manutenção | Tabela com prioridade   |
| Manutenção por equip.   | Resumo por equipamento        | Manutenção | Gráfico de barras       |

### 11.3 Resiliência do Dashboard

O dashboard **NÃO para de funcionar** se um serviço cair. A implementação segue o padrão:

```javascript
// Cada serviço é carregado independentemente com tratamento de erro individual
async function carregarDados() {
    // Sensores — carrega independente
    try {
        const leituras = await fetchJson(API.sensores + "/leituras/ultima");
        renderizarLeituras(leituras);
    } catch (error) {
        exibirIndisponivel("sensores", error);
    }

    // Alarmes — carrega independente
    try {
        const alarmes = await fetchJson(API.alarmes + "/alarmes/status/ativo");
        renderizarAlarmes(alarmes);
    } catch (error) {
        exibirIndisponivel("alarmes", error);
    }

    // Manutenção — carrega independente
    try {
        const ordens = await fetchJson(API.manutencao + "/ordens/status/aberta");
        renderizarOrdens(ordens);
    } catch (error) {
        exibirIndisponivel("manutencao", error);
    }
}

// Atualização periódica (a cada 30 segundos)
setInterval(carregarDados, 30000);
```

Quando um serviço se recupera, o próximo ciclo de atualização detecta automaticamente e restaura os dados.

### 11.4 Indicadores Visuais de Status

| Estado do Serviço   | Indicador Visual                                       |
|---------------------|--------------------------------------------------------|
| Disponível          | 🟢 Badge verde no cabeçalho da seção                  |
| Indisponível        | 🔴 Badge vermelho + mensagem "Serviço indisponível"   |
| Recuperado          | 🟢 Transição automática no próximo refresh             |

---

## 12. Chat com IA (Gemini)

### 12.1 Fluxo do Chat

```
Usuário digita pergunta
        │
        ▼
Chat envia mensagem + ferramentas MCP → Google Gemini API
        │
        ▼
Gemini decide: precisa de ferramenta?
    ├── NÃO → responde diretamente
    └── SIM → retorna function_call
                │
                ▼
        Chat executa ferramenta no MCP Server correspondente
                │
                ▼
        MCP Server acessa o serviço REST via HTTP interno
                │
                ▼
        Resultado retorna ao Gemini
                │
                ▼
        Gemini formula resposta em linguagem natural
                │
                ▼
        Resposta exibida ao usuário
```

### 12.2 Prompt do Sistema

```python
PROMPT = """
Você é o PlantaBot, assistente virtual do sistema de monitoramento
de planta industrial PlantaView. Você NÃO é uma pessoa real.

Quando o usuário fizer uma saudação, identifique-se pelo nome e
explique que pode ajudar com informações sobre sensores, alarmes
e manutenção dos equipamentos da planta.

Regras:
- Perguntas sobre leituras, temperaturas, pressões, vibrações →
  use ferramentas de sensores
- Perguntas sobre alarmes, limites excedidos, severidade →
  use ferramentas de alarmes
- Perguntas sobre ordens de serviço, manutenção, técnicos →
  use ferramentas de manutenção
- Perguntas fora do escopo → informe que não está capacitado
  e oriente o usuário a procurar o setor responsável

Equipamentos da planta:
1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2,
5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1
"""
```

### 12.3 Configuração

| Parâmetro      | Valor                     |
|----------------|---------------------------|
| Modelo         | `gemini-2.5-flash`        |
| Transporte MCP | `streamable-http`         |
| Endpoints MCP  | `localhost:8001-8003/mcp` |
| API Key        | Via `.env` (`GOOGLE_API_KEY`) |

---

## 13. Requisitos Não-Funcionais & Resiliência

### 13.1 Isolamento

- Cada serviço REST roda em seu próprio contêiner Docker
- Cada serviço possui seu próprio banco PostgreSQL em contêiner dedicado
- Cada servidor MCP roda em contêiner independente
- Falha em um serviço **não propaga** para os demais

### 13.2 Resiliência do Cliente

| Cenário                            | Comportamento Esperado                              |
|------------------------------------|-----------------------------------------------------|
| Serviço Sensores para              | Seções de leituras ficam indisponíveis; alarmes e manutenção seguem normais |
| Serviço Alarmes para               | Seções de alarmes ficam indisponíveis; sensores e manutenção seguem normais |
| Serviço Manutenção para            | Seções de manutenção ficam indisponíveis; sensores e alarmes seguem normais |
| Serviço retorna após queda         | Dashboard se recupera automaticamente no próximo ciclo de polling |
| Todos os serviços param            | Dashboard exibe todas as seções como indisponíveis  |

### 13.3 Restart Policy

Todos os contêineres utilizam `restart: always` para recuperação automática.

---

## 14. Seed de Dados

### 14.1 Equipamentos (compartilhado nos 3 bancos)

```sql
INSERT INTO plantaview.equipamentos (nome, tipo, localizacao) VALUES
('Bomba 1',       'bomba',       'Sala de Bombas'),
('Bomba 2',       'bomba',       'Sala de Bombas'),
('Compressor 1',  'compressor',  'Utilidades'),
('Compressor 2',  'compressor',  'Utilidades'),
('Compressor 3',  'compressor',  'Utilidades'),
('Motor 1',       'motor',       'Linha de Produção'),
('Motor 2',       'motor',       'Linha de Produção'),
('Caldeira 1',    'caldeira',    'Casa de Caldeiras');
```

### 14.2 Sensores (banco sensores)

```sql
-- 3 sensores por equipamento: temperatura, pressão, vibração
INSERT INTO plantaview.sensores (equipamento_id, grandeza, unidade, setpoint_min, setpoint_max) VALUES
-- Bomba 1
(1, 'temperatura', '°C',    20.00, 85.00),
(1, 'pressao',     'bar',    2.00, 10.00),
(1, 'vibracao',    'mm/s',   0.00,  7.00),
-- Bomba 2
(2, 'temperatura', '°C',    20.00, 85.00),
(2, 'pressao',     'bar',    2.00, 10.00),
(2, 'vibracao',    'mm/s',   0.00,  7.00),
-- Compressor 1
(3, 'temperatura', '°C',    15.00, 95.00),
(3, 'pressao',     'bar',    5.00, 15.00),
(3, 'vibracao',    'mm/s',   0.00, 10.00),
-- Compressor 2
(4, 'temperatura', '°C',    15.00, 95.00),
(4, 'pressao',     'bar',    5.00, 15.00),
(4, 'vibracao',    'mm/s',   0.00, 10.00),
-- Compressor 3
(5, 'temperatura', '°C',    15.00, 95.00),
(5, 'pressao',     'bar',    5.00, 15.00),
(5, 'vibracao',    'mm/s',   0.00, 10.00),
-- Motor 1
(6, 'temperatura', '°C',    25.00, 75.00),
(6, 'pressao',     'bar',    0.00,  0.00),
(6, 'vibracao',    'mm/s',   0.00,  5.00),
-- Motor 2
(7, 'temperatura', '°C',    25.00, 75.00),
(7, 'pressao',     'bar',    0.00,  0.00),
(7, 'vibracao',    'mm/s',   0.00,  5.00),
-- Caldeira 1
(8, 'temperatura', '°C',    50.00, 200.00),
(8, 'pressao',     'bar',    3.00, 10.00),
(8, 'vibracao',    'mm/s',   0.00,  4.00);
```

### 14.3 Volume de Dados de Seed

| Entidade         | Quantidade Estimada | Observação                            |
|------------------|---------------------|---------------------------------------|
| Equipamentos     | 8                   | Fixo                                  |
| Sensores         | 24                  | 3 por equipamento                     |
| Leituras         | ~500                | Simulando 3 dias de operação          |
| Alarmes          | ~40                 | Diversos status e severidades         |
| Ordens de Serviço| ~20                 | Diversos status e tipos               |

---

## 15. Estrutura de Diretórios do Projeto

```
PlantaView/
├── README.md
├── requirements.txt
├── SDD-PlantaIndustrial.md          ← este documento
│
├── servicos/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── dashboard.html               ← cliente web
│   │
│   ├── sensores/
│   │   ├── servico.py               ← Flask REST
│   │   └── init.sql                 ← DDL + seed do banco sensores
│   │
│   ├── alarmes/
│   │   ├── servico.py               ← Flask REST
│   │   └── init.sql                 ← DDL + seed do banco alarmes
│   │
│   └── manutencao/
│       ├── servico.py               ← Flask REST
│       └── init.sql                 ← DDL + seed do banco manutenção
│
└── mcp/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── .env.example
    ├── chat_google.py               ← chat IA com Gemini
    │
    ├── sensores/
    │   └── ferramentas.py           ← servidor MCP sensores
    │
    ├── alarmes/
    │   └── ferramentas.py           ← servidor MCP alarmes
    │
    └── manutencao/
        └── ferramentas.py           ← servidor MCP manutenção
```

---

## 16. Plano de Verificação

### 16.1 Testes Funcionais

| # | Teste                                              | Método                                       |
|---|----------------------------------------------------|----------------------------------------------|
| 1 | Serviços REST respondem em todas as rotas          | `curl` ou Postman para cada endpoint         |
| 2 | Dashboard exibe dados dos 3 serviços               | Abrir `dashboard.html` no navegador          |
| 3 | Dashboard sobrevive à queda de 1 serviço           | `docker stop sensores` → verificar dashboard |
| 4 | Dashboard se recupera ao reiniciar serviço         | `docker start sensores` → aguardar refresh   |
| 5 | Ferramentas MCP listadas no inspector              | `npx @modelcontextprotocol/inspector`        |
| 6 | Chat Gemini responde com dados dos 3 serviços      | Fazer as 3 perguntas de exemplo              |
| 7 | Chat aciona ferramenta correta por contexto        | Verificar logs do MCP                        |

### 16.2 Comandos de Inicialização

```bash
# 1. Criar rede compartilhada
docker network create rede-plantaview

# 2. Subir serviços REST + bancos de dados
cd servicos
docker compose up -d --build

# 3. Subir serviços MCP
cd ../mcp
docker compose up -d --build

# 4. Abrir dashboard
# Abrir servicos/dashboard.html no navegador

# 5. Iniciar chat
cd ../mcp
python chat_google.py
```

### 16.3 Inspeção MCP

```bash
# Inspecionar um serviço MCP individualmente
fastmcp inspect sensores/ferramentas.py

# Inspector visual (web)
npx @modelcontextprotocol/inspector
```

---

## 17. Rastreabilidade de Requisitos

Mapeamento dos requisitos do PDF `IFBA-SOA-Avaliacao-v3.0` para os componentes do projeto:

| Req. | Descrição do Requisito                                        | Componente(s) que Atende                                |
|------|---------------------------------------------------------------|---------------------------------------------------------|
| 5    | Três ou mais serviços, cada um faz UMA coisa                  | `sensores/`, `alarmes/`, `manutencao/` — cada um isolado |
| 6    | Contêineres adicionais de suporte (BD)                        | `dados-sensores`, `dados-alarmes`, `dados-manutencao`    |
| 7    | Arquitetura RESTful + Docker + isolamento por contêiner       | Flask + `docker-compose.yml` + Dockerfiles               |
| 8    | Cliente resiliente à queda de serviços                        | `dashboard.html` — try/catch independente por serviço    |
| 9    | Ferramentas MCP para cada serviço acessíveis por IA           | `mcp/sensores/`, `mcp/alarmes/`, `mcp/manutencao/`      |
| 10   | Pelo menos 2 rotas/endpoints acessadas pelo MCP               | Cada MCP expõe 3 ferramentas (≥ 2 rotas cada)            |
| 11   | Chat com OpenAI ou Google AI                                  | `chat_google.py` com Google Gemini                       |
| 13   | Entrega de fontes, Dockerfiles e scripts de BD                | Estrutura completa de diretórios documentada             |

---

> **Documento preparado segundo a técnica SDD (IEEE 1016) adaptada para o contexto acadêmico. Pronto para servir como base de implementação do projeto PlantaView.**
