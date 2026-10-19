import asyncio
import json
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from google import genai

MODELO = "gemini-3.6-flash"
PROMPT = """

Você é o PlantaBot, assistente virtual do sistema de monitoramento de planta industrial PlantaView.
Você não é uma pessoa real, é um assistente virtual.

Quando o usuário fizer uma saudação ou iniciar uma conversa contigo, identifique-se pelo seu nome
e informe que pode ajudar com informações sobre sensores, alarmes e manutenção dos equipamentos da planta.

Quando o usuário solicitar informações, utilize as ferramentas MCP disponíveis. Obedeça estas regras:

- perguntas sobre leituras, temperaturas, pressões, vibrações → use ferramentas de sensores
- perguntas sobre alarmes, limites excedidos, severidade → use ferramentas de alarmes
- perguntas sobre ordens de serviço, manutenção, técnicos → use ferramentas de manutenção
- perguntas fora do escopo → diga que não está capacitado e oriente o usuário a procurar o setor responsável

Equipamentos da planta:
1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2,
5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1

"""

load_dotenv()

SERVICOS_MCP = {
    "sensores":     "http://localhost:8001/mcp",
    "alarmes":      "http://localhost:8002/mcp",
    "manutencao":   "http://localhost:8003/mcp",
}

async def iniciar():
    iniciado, stack, cliente_IA = False, AsyncExitStack(), None

    try:
        cliente_IA = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        iniciado = True
    except Exception as e:
        print(f"⚠️ erro iniciando conexão com IA: {e}")

    return iniciado, stack, cliente_IA

async def conectar_servicos(stack):
    servicos = {}

    for nome_servico, url in SERVICOS_MCP.items():
        stream_leitura, stream_escrita = await stack.enter_async_context(streamable_http_client(url))

        conexao = await stack.enter_async_context(
            ClientSession(stream_leitura, stream_escrita)
        )
        await conexao.initialize()

        servicos[nome_servico] = conexao
        print(f"conectado ao serviço, '{nome_servico}'")

    return servicos

async def get_ferramentas(servicos):
    ferramentas = {}

    for nome_servico, conexao in servicos.items():
        resultado = await conexao.list_tools()

        for ferramenta in resultado.tools:
            ferramentas[ferramenta.name] = {
                "servico": {
                    "nome": nome_servico,
                    "conexao": conexao
                },
                "ferramenta": {
                    "type": "function",
                    "name": ferramenta.name,
                    "description": ferramenta.description,
                    "parameters": ferramenta.input_schema,
                }
            }

    return ferramentas

async def executar_ferramenta(ferramentas, ferramenta_desejada, argumentos):
    ferramenta = ferramentas[ferramenta_desejada]

    servico = ferramenta['servico']
    print(f"🤖 executando a ferramenta, '{ferramenta_desejada}', do serviço, '{servico['nome']}'")
    
    conexao = servico['conexao']
    resultado = await conexao.call_tool(ferramenta_desejada, arguments = argumentos)

    return extrair_texto(resultado)

def extrair_texto(resultado):
    if resultado.structured_content:
        return json.dumps(resultado.structured_content, ensure_ascii=False)

    conteudo = []
    for c in resultado.content:
        if hasattr(c, "text"):
            conteudo.append(c.text)
        else:
            conteudo.append(str(c))

    return "\n".join(conteudo)

async def chat(cliente_IA, ferramentas):
    mensagens = [
        {
            "type": "user_input",
            "content": [{ "type": "text", "text": PROMPT }]
        }
    ]

    while True:
        mensagem = input("\n👤 ")
        mensagem = mensagem.lower()

        if mensagem in [ "sair", "/s" ]:
            break

        mensagens.append({
            "type": "user_input",
            "content": [{ "type": "text", "text": mensagem }]
        })

        while True:
            resposta = await cliente_IA.aio.interactions.create(
                model = MODELO,
                input = mensagens,
                tools = [f["ferramenta"] for f in ferramentas.values()]
            )

            execucoes = [item for item in resposta.steps if item.type == "function_call"]
            if not execucoes:
                print(f"🤖 {resposta.output_text}")

                break

            mensagens.extend(resposta.steps)
            for execucao in execucoes:
                argumentos = execucao.arguments
                resultado = await executar_ferramenta(ferramentas, execucao.name, argumentos)

                mensagens.append({
                    "type": "function_result",
                    "name": execucao.name,
                    "call_id": execucao.id,
                    "result": [{ "type": "text", "text": resultado}]
                })

async def finalizar(stack):
    await stack.aclose()

async def executar():
    iniciado, stack, cliente_IA = await iniciar()
    if iniciado:
        try:
            servicos = await conectar_servicos(stack)
            ferramentas = await get_ferramentas(servicos)

            await chat(cliente_IA, ferramentas)
        finally:
            await finalizar(stack)

if __name__ == "__main__":
    asyncio.run(executar())
