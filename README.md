# 🏭 PlantaBot — Sistema Especialista para Supervisão e Manutenção de Planta Industrial

🎓 **Atividade Acadêmica**  
Projeto desenvolvido para a disciplina **Sistemas Especialistas para Web**  
**Curso:** Pós-Graduação em Desenvolvimento para Web  
**Instituição:** Instituto Federal de Educação, Ciência e Tecnologia da Bahia ([IFBA](https://portal.ifba.edu.br/))  
**Professor:** Luis Paulo da Silva Carvalho  

---

## 📌 Visão Geral

O **PlantaBot** é um agente inteligente e sistema especialista conversacional voltado ao diagnóstico operacional, supervisão de sensores, análise de alarmes de limite excedido (*setpoints*) e gestão de manutenção (preventiva, preditiva e corretiva) de uma planta industrial de pequeno porte (**PlantaView**).

O sistema integra Modelos de Linguagem de Larga Escala (LLMs) executados localmente através do **Ollama**, combinando:
- **Engenharia de Prompt, Persona Especialista e Base de Conhecimento Estruturada (`conhecimento/planta.json`)**;
- **Restrição de Escopo (*Guardrails*)**;
- **Ferramentas MCP (*Model Context Protocol*)** para consulta de telemetria, alarmes e ordens de serviço em tempo real (`ferramentas.py` e microsserviços em `servicos/` e `servidores_mcp/`);
- **Cache Semântico Vetorial (`cache.py`)** com embeddings (`SentenceTransformer`) e `ChromaDB`;
- **Avaliação Automatizada com LLM-as-a-Judge (`julgamento.py`)** e testes unitários (`teste.py`).

---

## 🚀 Principais Funcionalidades

- **Persona Especialista (`PlantaBot`):** Atua estritamente como especialista em instrumentação, supervisão e manutenção industrial dos 8 equipamentos da planta (*Bombas 1 e 2, Compressores 1 a 3, Motores 1 e 2, e Caldeira 1*).
- **Restrição de Domínio (*Guardrails*):** Caso receba perguntas fora do escopo industrial, o assistente recusa educadamente o atendimento (`"não posso responder esta pergunta"`).
- **Cache Semântico com Embeddings (`cache.py`):** Antes de acionar o LLM/MCP, o sistema gera embeddings da pergunta com `paraphrase-multilingual-MiniLM-L12-v2` e consulta uma coleção vetorial no `ChromaDB` (distância de cosseno $\le 0.20$). Perguntas semanticamente equivalentes são respondidas com a indicação `[recuperada do cache]`. Respostas obtidas com ferramentas MCP (estado da planta naquele instante) e recusas de escopo não são gravadas no cache.
- **Ferramentas MCP (`ferramentas.py`):** Exposição de ferramentas via *Model Context Protocol* (`streamable-http`) para consulta de leituras de sensores, alarmes por severidade e ordens de serviço, integrando-se aos microsserviços REST/PostgreSQL (`servicos/`). Se eles estiverem desligados, as ferramentas devolvem dados simulados de contingência, identificados no campo `fonte`, e o chat avisa o operador.
- **Validação com LLM-as-a-Judge (`julgamento.py`):** Um modelo julgador (`mistral:latest`) avalia automaticamente se as respostas do assistente (`qwen3:4b`) atendem aos critérios técnicos (`ATENDE`) e rejeita alucinações deliberadas (`NÃO ATENDE`).
- **Memória da conversa:** as últimas 8 mensagens da sessão acompanham cada nova pergunta (`LIMITE_HISTORICO` em `chat.py`).
- **Testes Automatizados (`teste.py`):** Suíte `unittest` para validação de assertividade conceitual e filtros de escopo.

---

## 🏗️ Arquitetura do Sistema

```mermaid
flowchart TD
    Usuario([👤 Operador / Supervisor]) -->|Faz uma pergunta| Chat[chat.py]
    Chat -->|Consulta pergunta| Cache[cache.py: Cache Semântico]
    Cache -->|SentenceTransformer + ChromaDB| CosineCheck{Distância Cosseno <= 0.20?}
    CosineCheck -- Sim (Hit) --> RespostaCache["🤖 Resposta [recuperada do cache]"]
    RespostaCache --> Usuario
    CosineCheck -- Não (Miss) --> LLMCall[llm.py: Cliente OpenAI -> Ollama]
    LLMCall <-->|Tool Call MCP / HTTP| MCPServer[ferramentas.py: Servidor MCP]
    MCPServer <-->|REST / SQL ou Dados Determinísticos| Servicos[(Microsserviços: Sensores, Alarmes, Manutenção)]
    LLMCall -->|Prompt + Persona + Conhecimento| OllamaLocal[(Ollama: Qwen)]
    OllamaLocal --> RespostaLLM["🤖 Resposta [resposta do llm]"]
    RespostaLLM --> GravarCache[Salva no ChromaDB]
    GravarCache --> Usuario
```

---

## 📂 Estrutura de Arquivos

```text
supervisorio-especialista/
│
├── conhecimento/
│   ├── planta.json           # Base de conhecimento estruturada da planta industrial (20 itens)
│   └── planta_menor.json     # Subconjunto enxuto para avaliação rápida no LLM-as-a-Judge
│
├── cache/                    # Diretório de persistência do banco vetorial ChromaDB
│
├── servidores_mcp/           # Servidores MCP containerizados (Sensores :8001, Alarmes :8002, Manutenção :8003)
├── servicos/                 # Microsserviços REST Flask + PostgreSQL + Dashboard Web (dashboard.html)
│
├── cache.py                  # Gerenciamento de cache semântico (SentenceTransformer + ChromaDB)
├── ferramentas.py            # Servidor MCP unificado de ferramentas da planta (porta 8000)
├── llm.py                    # Comunicação com o servidor local do Ollama via API OpenAI
├── chat.py                   # Interface interativa de terminal e ciclo principal do especialista PlantaBot
├── julgamento.py             # Pipeline de avaliação com LLM-as-a-Judge e detecção de alucinações
├── teste.py                  # Testes de unidade automatizados (unittest)
├── requirements.txt          # Dependências Python do projeto
├── SDD-PlantaIndustrial.md   # Documento de especificação de projeto (Software Design Description)
└── README.md                 # Documentação do projeto
```

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Servidor de LLM Local:** [Ollama](https://ollama.com/)
  - **Modelo Assistente:** `qwen3:4b`
  - **Modelo Julgador:** `mistral:latest`
- **Embeddings & Vetorização:** `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Banco Vetorial:** `chromadb` (persistência local com distância de cosseno)
- **Servidor e Cliente MCP:** `fastmcp` / `mcp` (`streamable-http`)
- **Cliente LLM:** `openai` (consumindo endpoint compatível do Ollama em `http://localhost:11434/v1/`)
- **Framework de Testes:** `unittest`

---

## ⚙️ Como Configurar e Executar

### 1. Clonar o repositório
```bash
git clone https://github.com/sidgubert/supervisorio-especialista.git
cd supervisorio-especialista
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Iniciar o Ollama e baixar os modelos
Certifique-se de que o Ollama está rodando em `http://localhost:11434` e que os modelos estão disponíveis:
```bash
ollama pull qwen3:4b
ollama pull mistral:latest
```
Os modelos podem ser trocados sem editar o código, pelas variáveis de ambiente `PLANTABOT_MODELO` (assistente) e `PLANTABOT_MODELO_JULGADOR` (julgador).

### 5. (Opcional) Iniciar o Servidor de Ferramentas MCP
Em um terminal separado, inicie o servidor MCP local em `http://127.0.0.1:8000/mcp`:
```bash
python ferramentas.py
```
*(Caso deseje subir também os microsserviços Docker completos com PostgreSQL e o Dashboard Web, consulte as instruções em `SDD-PlantaIndustrial.md`).*

---

## ▶️ Execução dos Módulos

### 💬 1. Conversar com o Especialista (PlantaBot)
```bash
python chat.py
```
O sistema indicará se a resposta foi obtida via cache vetorial `[recuperada do cache]` ou processada pelo modelo `[resposta do llm]`.

### ⚖️ 2. Executar o Julgamento Automatizado (LLM-as-a-Judge)
Executa a rotina em duas etapas: o julgador precisa reprovar 3 respostas erradas do domínio (`NÃO ATENDE`) e aprovar as respostas do assistente às 4 perguntas de `conhecimento/planta_menor.json` (`ATENDE`). Ao final é impresso o placar, e o script termina com erro se algum veredito não for o esperado:
```bash
python julgamento.py
```

### 🧪 3. Executar os Testes Automatizados
Executa os testes unitários de assertividade conceitual e bloqueio de perguntas fora do domínio (*guardrails*):
```bash
python teste.py
```

---

## 📝 Mudanças desta versão

**Código**
- `chat.py`: memória da conversa (últimas 8 mensagens); respostas obtidas com ferramentas não vão mais para o cache; limite de 5 rodadas de ferramentas por pergunta; aviso ao operador quando a ferramenta devolve dados simulados; regra de escopo reforçada e resposta sempre em português; modelo configurável por `PLANTABOT_MODELO`.
- `llm.py`: a inicialização agora confirma que o Ollama está no ar antes de informar "ollama iniciado".
- `ferramentas.py`: aceita o equipamento por id ou por nome ("Caldeira 1"); valida grandeza, severidade e status; informa a origem dos dados no campo `fonte`; o diagnóstico considera também o setpoint mínimo; o servidor escuta apenas em `127.0.0.1`.
- `julgamento.py`: alucinações do próprio domínio industrial; exige o veredito `ATENDE` para aprovar (antes bastava não conter `NÃO ATENDE`); placar final; julgador configurável por `PLANTABOT_MODELO_JULGADOR`.
- `teste.py`: importações explícitas (antes o teste rodava, sem aviso, com o modelo do julgador).
- Modelos: assistente `qwen3:4b` e julgador `mistral:latest`. O `qwen2.5:1.5b` foi descartado como assistente porque, nos testes, respondeu perguntas fora do domínio e nem sempre acionou as ferramentas.

**Organização**
- Pasta `mcp/` renomeada para `servidores_mcp/` (o nome antigo colidia com a biblioteca `mcp` do Python).
- Removidos `mcp/testa_chave.py` e `Livro_SE_Capitulo_PlantaBot.zip` (cópia duplicada de `livro_se/`).
- `cache/` incluído no `.gitignore`; `google-genai` incluído no `requirements.txt` (usado por `servidores_mcp/chat_google.py`).

**Capítulo do livro (`livro_se/capitulos/capitulo_2/`)**
- Texto reescrito para descrever apenas o que o código faz.
- Figuras de funcionamento e de julgamento geradas a partir da saída real de `python chat.py` e `python julgamento.py`.
- Pendente: substituir os links do Zenodo (código e vídeo) pelos definitivos.
