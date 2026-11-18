# Roteiro do vídeo — PlantaBot

Limite do descritivo: **8 minutos**, com som e imagem. O vídeo precisa mostrar (i) o tema, (ii) como iniciar o sistema e avaliá-lo com o julgador e (iii) o funcionamento da solução, deixando claros os quatro módulos: **LLM, cache semântico, ferramentas MCP e LLM-as-a-Judge**.

Tempo total previsto: cerca de 7 min 30 s.

## Antes de gravar

- Ollama no ar, com o `qwen3:4b` baixado (`ollama pull qwen3:4b`).
- `.env` com a `GOOGLE_API_KEY` válida.
- Apagar a pasta `cache/`, para a primeira pergunta conceitual não sair do cache.
- Deixar os microsserviços de `servicos/` desligados (a ferramenta usa dados de contingência; é o cenário que o avaliador vai encontrar).
- Fazer um ensaio completo: o `julgamento.py` leva alguns minutos. Se passar do tempo, grave-o à parte e acelere o trecho na edição.
- Dois terminais lado a lado, fonte grande.

## 1. Tema (0:00 – 0:45)

- Apresentação: nome, disciplina Sistemas Especialistas para Web (IFBA).
- O PlantaBot emula um engenheiro de instrumentação e manutenção de uma planta industrial com 8 equipamentos (bombas, compressores, motores, caldeira), monitorados por sensores de temperatura, pressão e vibração.
- Ele responde dúvidas conceituais e consulta o estado da planta: leituras, alarmes e ordens de serviço.

## 2. Os quatro módulos no código (0:45 – 2:15)

Mostrar cada arquivo por uns 20 segundos, apontando o trecho principal:

| Módulo | Arquivo | O que mostrar |
|---|---|---|
| LLM | `llm.py` | Cliente OpenAI apontando para o Ollama (`qwen3:4b`) |
| Cache semântico | `cache.py` | Embeddings com `sentence-transformers` e busca no ChromaDB (cosseno ≤ 0,20) |
| Ferramentas MCP | `ferramentas.py` | Um `@mcp.tool` (por exemplo `diagnosticar_equipamento`) e o servidor em `127.0.0.1:8000/mcp` |
| Cliente MCP | `chat.py` | `conectar_ferramentas`: lista as ferramentas do servidor e as entrega ao LLM |
| LLM-as-a-Judge | `julgamento.py` | Gemini como julgador; vereditos `ATENDE` / `NÃO ATENDE` |

## 3. Como iniciar (2:15 – 3:00)

Terminal 1:

```bash
python ferramentas.py
```

Terminal 2:

```bash
python chat.py
```

Destacar a linha `conectado ao servidor MCP 'supervisao_planta_industrial' ... 10 ferramentas disponíveis`.

## 4. Funcionamento (3:00 – 5:45)

Uma pergunta por módulo, nesta ordem:

1. **Saudação:** `Olá` → o PlantaBot se apresenta como software especialista.
2. **LLM:** `O que é um setpoint em automação industrial?` → marcado `[resposta do llm]`.
3. **Cache semântico:** `Explique o que significa setpoint na automação` → marcado `[recuperada do cache]`, quase instantâneo.
4. **Ferramenta MCP:** `Faça o diagnóstico da Caldeira 1` → aparece `🤖 executando a ferramenta MCP 'diagnosticar_equipamento'` e o aviso de dados simulados de contingência. Explicar que respostas de ferramentas não vão para o cache, porque mudam com o tempo.
5. **Outra ferramenta:** `Quais alarmes críticos estão ativos?` → `alarmes_por_severidade`.
6. **Fora do domínio:** `Qual é a capital da França?` → `não posso responder esta pergunta`.

Encerrar com `sair`.

## 5. Avaliação com o julgador (5:45 – 7:15)

```bash
python julgamento.py
```

- Etapa 1: o Gemini precisa reprovar 3 respostas erradas (alucinações do domínio) → `NÃO ATENDE`.
- Etapa 2: o Gemini avalia as respostas do `qwen3:4b` às 4 perguntas de `conhecimento/planta_menor.json` → `ATENDE`.
- Mostrar o placar final.

## 6. Fechamento (7:15 – 7:30)

- Recapitular: chat, LLM local, cache semântico, servidor MCP e julgador.
- Código e vídeo disponíveis no Zenodo (links no capítulo, seção Reprodutibilidade e Reuso).
