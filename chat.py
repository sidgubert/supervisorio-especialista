import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import urlparse

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from cache import buscar_cache, gravar_cache, iniciar_cache
from llm import iniciar_ollama, limpar_pensamento, obter_resposta, obter_resposta_com_ferramentas

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIRETORIO_BASE = Path(__file__).resolve().parent

NOME_ESPECIALISTA = "PlantaBot"
BASE_CONHECIMENTO = DIRETORIO_BASE / "conhecimento" / "planta.json"
# o modelo do assistente pode ser trocado sem editar o código: defina PLANTABOT_MODELO
MODELO = os.environ.get("PLANTABOT_MODELO", "qwen3:4b")

CACHE = DIRETORIO_BASE / "cache"
MODELO_CACHE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
NOME_CACHE = "plantabot_cache"
COMANDOS_SAIDA = {"sair", "exit", "quit", "/s"}
RESPOSTA_RECUSA = "não posso responder esta pergunta"

# memória de trabalho: quantas mensagens anteriores (usuário + assistente)
# acompanham cada nova pergunta enviada ao LLM
LIMITE_HISTORICO = 8
# teto de rodadas de ferramentas por pergunta, para o modelo não ficar em laço
LIMITE_RODADAS_FERRAMENTAS = 5

URL_FERRAMENTAS = "http://127.0.0.1:8000/mcp"
SERVICOS_MCP_DOCKER = {
    "sensores": "http://localhost:8001/mcp",
    "alarmes": "http://localhost:8002/mcp",
    "manutencao": "http://localhost:8003/mcp",
}


def iniciar_persona_assistente(conhecimento: list[tuple[str, str]]) -> list[dict[str, str]]:
    diretrizes_conhecimento = "\n".join(
        f"- Pergunta: '{pergunta}' -> Resposta: '{resposta}'"
        for pergunta, resposta in conhecimento
    )

    conteudo_sistema = (
        f"Você é um especialista, perito, em supervisão, diagnóstico operacional e manutenção de planta industrial, chamado {NOME_ESPECIALISTA}.\n"
        "Responda sempre em português do Brasil.\n"
        "Regras:\n"
        "1. Se o usuário fizer uma saudação, você deve falar na sua resposta que você é um software, "
        "não é um humano, mas que pode ajudar o usuário com diagnóstico de sensores, alarmes e manutenção dos equipamentos da planta industrial.\n"
        "2. Equipamentos monitorados na planta: 1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1.\n"
        "3. Quando o usuário pedir o estado atual, leituras, alarmes, ordens de serviço ou o diagnóstico de um equipamento, "
        "execute as ferramentas disponíveis e responda somente com os dados retornados por elas, sem inventar valores.\n"
        "4. Se o resultado de uma ferramenta trouxer o campo 'fonte' indicando contingência, avise na resposta que os dados são simulados.\n"
        "5. Caso o usuário fale ou pergunte algo parecido com os itens abaixo, utilize a respectiva resposta:\n"
        f"{diretrizes_conhecimento}\n"
        # a regra de escopo fica por último e com exemplos: modelos pequenos
        # dão mais peso ao fim do prompt e ignoravam a regra quando ela vinha no meio
        "6. REGRA MAIS IMPORTANTE: você só responde sobre supervisão industrial, sensores, alarmes, equipamentos e manutenção da planta. "
        "Para qualquer outro assunto (história, geografia, esportes, culinária, entretenimento, programação, etc.) "
        f"você deve dizer apenas '{RESPOSTA_RECUSA}', sem acrescentar mais nada.\n"
        f"Exemplo: usuário pergunta 'Qual é a capital da França?' -> você responde '{RESPOSTA_RECUSA}'.\n"
        f"Exemplo: usuário pergunta 'Me indique um filme' -> você responde '{RESPOSTA_RECUSA}'."
    )

    return [{"role": "system", "content": conteudo_sistema}]


def carregar_conhecimento(base_conhecimento: Path | str = BASE_CONHECIMENTO) -> tuple[bool, list[tuple[str, str]]]:
    try:
        with open(base_conhecimento, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)

        conhecimento = [
            (pergunta_resposta["pergunta"], pergunta_resposta["resposta"])
            for pergunta_resposta in conteudo
        ]

        return True, conhecimento
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"erro carregando conhecimento: {e}")
        return False, []


async def servidor_disponivel(url: str, timeout: float = 1.5) -> bool:
    endereco = urlparse(url)
    try:
        _, escritor = await asyncio.wait_for(
            asyncio.open_connection(endereco.hostname, endereco.port or 80),
            timeout=timeout
        )
        escritor.close()
        await escritor.wait_closed()
        return True
    except Exception:
        return False


async def conectar_ferramentas(contexto: AsyncExitStack) -> tuple[dict[str, dict], list[dict]]:
    mapa_ferramentas = {}
    ferramentas_openai = []

    urls_ativas = {}
    if await servidor_disponivel(URL_FERRAMENTAS):
        urls_ativas["supervisao_planta_industrial"] = URL_FERRAMENTAS
    else:
        for nome_srv, url_srv in SERVICOS_MCP_DOCKER.items():
            if await servidor_disponivel(url_srv):
                urls_ativas[nome_srv] = url_srv

    if not urls_ativas:
        print(f"servidor de ferramentas MCP indisponível em {URL_FERRAMENTAS}. Para consultas MCP em tempo real, execute 'python ferramentas.py'.")
        return mapa_ferramentas, ferramentas_openai

    for nome_servico, url in urls_ativas.items():
        try:
            stream_leitura, stream_escrita = await contexto.enter_async_context(streamable_http_client(url))
            conexao = await contexto.enter_async_context(ClientSession(stream_leitura, stream_escrita))
            await conexao.initialize()

            listagem = await conexao.list_tools()
            for f in listagem.tools:
                mapa_ferramentas[f.name] = {
                    "servico": nome_servico,
                    "conexao": conexao
                }
                ferramentas_openai.append({
                    "type": "function",
                    "function": {
                        "name": f.name,
                        "description": f.description,
                        "parameters": f.inputSchema if hasattr(f, "inputSchema") else getattr(f, "input_schema", {})
                    }
                })
            print(f"conectado ao serviço MCP '{nome_servico}' ({url})")
        except Exception as e:
            print(f"erro conectando ao serviço MCP '{nome_servico}': {e}")

    return mapa_ferramentas, ferramentas_openai


def extrair_texto_execucao(resultado) -> str:
    if getattr(resultado, "structured_content", None):
        return json.dumps(resultado.structured_content, ensure_ascii=False)

    conteudo = []
    for c in resultado.content:
        if hasattr(c, "text"):
            conteudo.append(c.text)
        else:
            conteudo.append(str(c))

    return "\n".join(conteudo)


async def executar_ferramenta(mapa_ferramentas, nome_ferramenta, argumentos) -> str:
    if nome_ferramenta not in mapa_ferramentas:
        return f"ferramenta '{nome_ferramenta}' não encontrada"

    info = mapa_ferramentas[nome_ferramenta]
    print(f"🤖 executando a ferramenta MCP '{nome_ferramenta}' do serviço '{info['servico']}' com {argumentos}")

    try:
        execucao = await info["conexao"].call_tool(nome_ferramenta, arguments=argumentos)
        resultado = extrair_texto_execucao(execucao)
        # o aviso não depende do LLM: se a ferramenta usou dados de contingência, o operador fica sabendo
        if "contingência" in resultado:
            print("⚠️ microsserviços da planta indisponíveis: a ferramenta devolveu dados simulados de contingência")
        return resultado
    except Exception as e:
        return f"erro executando a ferramenta '{nome_ferramenta}': {e}"


async def processar_pergunta(ollama, persona, historico, mensagem, mapa_ferramentas, ferramentas_openai, modelo=MODELO):
    """Envia a pergunta ao LLM junto com a persona e o histórico da sessão.

    Retorna (sucesso, resposta, ferramentas_executadas).
    """
    mensagens = persona + historico + [{"role": "user", "content": mensagem}]
    ferramentas_executadas = False

    if not ferramentas_openai:
        sucesso, resposta = obter_resposta(ollama, mensagens, modelo=modelo)
        return sucesso, resposta, ferramentas_executadas

    for _ in range(LIMITE_RODADAS_FERRAMENTAS):
        sucesso, msg_resposta = obter_resposta_com_ferramentas(
            ollama, mensagens, ferramentas=ferramentas_openai, modelo=modelo
        )
        if not sucesso or msg_resposta is None:
            return False, None, ferramentas_executadas

        chamadas = getattr(msg_resposta, "tool_calls", None)
        if not chamadas:
            texto_final = limpar_pensamento(msg_resposta.content or "")
            return True, texto_final, ferramentas_executadas

        ferramentas_executadas = True
        mensagens.append({
            "role": "assistant",
            "content": msg_resposta.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in chamadas
            ]
        })

        for tc in chamadas:
            try:
                argumentos = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
            except Exception:
                argumentos = {}

            mensagens.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.function.name,
                "content": await executar_ferramenta(mapa_ferramentas, tc.function.name, argumentos or {})
            })

    # o modelo esgotou as rodadas pedindo ferramentas: exige a resposta final só com o que já foi coletado
    sucesso, resposta = obter_resposta(ollama, mensagens, modelo=modelo)
    return sucesso, resposta, ferramentas_executadas


def registrar_historico(historico, mensagem, resposta) -> None:
    historico.append({"role": "user", "content": mensagem})
    historico.append({"role": "assistant", "content": resposta})
    del historico[:-LIMITE_HISTORICO]


async def executar_async() -> None:
    iniciado, ollama = iniciar_ollama()
    if not iniciado:
        return
    print("ollama iniciado")

    carregado, conhecimento = carregar_conhecimento()
    if not carregado:
        return
    print("conhecimento carregado")

    iniciado, modelo_cache, colecao_cache = iniciar_cache(MODELO_CACHE, CACHE, NOME_CACHE)
    if not iniciado:
        return
    print("cache iniciado, aguardando mensagens... (digite 'sair' para encerrar)")

    persona = iniciar_persona_assistente(conhecimento)
    historico = []

    async with AsyncExitStack() as contexto:
        mapa_ferramentas, ferramentas_openai = await conectar_ferramentas(contexto)

        try:
            while True:
                mensagem = input("👤 ").strip()
                if not mensagem:
                    continue
                if mensagem.lower() in COMANDOS_SAIDA:
                    print("🤖 Até logo!")
                    break

                encontrada, resposta = buscar_cache(mensagem, modelo_cache, colecao_cache)
                if encontrada:
                    print(f"🤖 {resposta} [recuperada do cache]")
                    registrar_historico(historico, mensagem, resposta)
                    continue

                sucesso, resposta, ferramentas_executadas = await processar_pergunta(
                    ollama, persona, historico, mensagem, mapa_ferramentas, ferramentas_openai, modelo=MODELO
                )

                if sucesso and resposta:
                    print(f"🤖 {resposta} [resposta do llm]")
                    registrar_historico(historico, mensagem, resposta)

                    # respostas montadas com ferramentas refletem o estado da planta naquele instante
                    # e recusas não são conhecimento: nenhuma das duas vai para o cache
                    if not ferramentas_executadas and RESPOSTA_RECUSA not in resposta.lower():
                        gravar_cache(mensagem, resposta, modelo_cache, colecao_cache)
                else:
                    print("🤖 não sei responder esta pergunta, pergunte outra coisa sobre supervisão e manutenção da planta industrial")
        except (KeyboardInterrupt, EOFError):
            print("\n🤖 Encerrando o PlantaBot.")


def executar() -> None:
    asyncio.run(executar_async())


if __name__ == "__main__":
    executar()
