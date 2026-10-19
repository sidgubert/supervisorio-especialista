import asyncio
import json
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from cache import buscar_cache, gravar_cache, iniciar_cache
from llm import iniciar_ollama, limpar_pensamento, obter_resposta, obter_resposta_com_ferramentas

DIRETORIO_BASE = Path(__file__).resolve().parent


def _importar_mcp_cliente():
    caminho_atual = str(DIRETORIO_BASE)
    caminhos_originais = list(sys.path)
    try:
        sys.path = [p for p in sys.path if p not in ("", ".", caminho_atual)]
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
        return ClientSession, streamable_http_client
    except ImportError:
        return None, None
    finally:
        sys.path = caminhos_originais


ClientSession, streamable_http_client = _importar_mcp_cliente()

NOME_ESPECIALISTA = "PlantaBot"
BASE_CONHECIMENTO = DIRETORIO_BASE / "conhecimento" / "planta.json"
MODELO = "qwen2.5:1.5b"

CACHE = DIRETORIO_BASE / "cache"
MODELO_CACHE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
NOME_CACHE = "plantabot_cache"
COMANDOS_SAIDA = {"sair", "exit", "quit", "/s"}
RESPOSTA_RECUSA = "não posso responder esta pergunta"

URL_FERRAMENTAS = "http://localhost:8000/mcp"
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
        "Regras:\n"
        "1. Se o usuário fizer uma saudação, você deve falar na sua resposta que você é um software, "
        "não é um humano, mas que pode ajudar o usuário com diagnóstico de sensores, alarmes e manutenção dos equipamentos da planta industrial.\n"
        "2. Se o usuário te perguntar algo que não esteja relacionado com supervisão industrial, sensores, alarmes, equipamentos ou manutenção da planta, "
        f"você deve dizer '{RESPOSTA_RECUSA}'.\n"
        "3. Equipamentos monitorados na planta: 1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1.\n"
        "4. Caso o usuário fale ou pergunte algo parecido com os itens abaixo, utilize a respectiva resposta:\n"
        f"{diretrizes_conhecimento}"
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

    if ClientSession is None or streamable_http_client is None:
        return mapa_ferramentas, ferramentas_openai

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


async def processar_pergunta(ollama, persona, mensagem, mapa_ferramentas, ferramentas_openai, modelo=MODELO):
    mensagens = persona + [{"role": "user", "content": mensagem}]
    ferramentas_executadas = False

    if not ferramentas_openai:
        sucesso, resposta = obter_resposta(ollama, mensagens, modelo=modelo)
        return sucesso, resposta, ferramentas_executadas

    while True:
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
            nome_ferramenta = tc.function.name
            try:
                argumentos = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
            except Exception:
                argumentos = {}

            if nome_ferramenta in mapa_ferramentas:
                info = mapa_ferramentas[nome_ferramenta]
                print(f"🤖 executando a ferramenta MCP '{nome_ferramenta}' do serviço '{info['servico']}'...")
                execucao = await info["conexao"].call_tool(nome_ferramenta, arguments=argumentos)
                resultado_texto = extrair_texto_execucao(execucao)
            else:
                resultado_texto = f"ferramenta '{nome_ferramenta}' não encontrada"

            mensagens.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": nome_ferramenta,
                "content": resultado_texto
            })


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
                    continue

                sucesso, resposta, _ = await processar_pergunta(
                    ollama, persona, mensagem, mapa_ferramentas, ferramentas_openai, modelo=MODELO
                )

                if sucesso and resposta:
                    print(f"🤖 {resposta} [resposta do llm]")

                    if RESPOSTA_RECUSA not in resposta.lower():
                        gravar_cache(mensagem, resposta, modelo_cache, colecao_cache)
                else:
                    print("🤖 não sei responder esta pergunta, pergunte outra coisa sobre supervisão e manutenção da planta industrial")
        except (KeyboardInterrupt, EOFError):
            print("\n🤖 Encerrando o PlantaBot.")


def executar() -> None:
    asyncio.run(executar_async())


if __name__ == "__main__":
    executar()
