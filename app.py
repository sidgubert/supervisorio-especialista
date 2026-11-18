"""Interface web do PlantaBot, feita com Chainlit.

Reaproveita do chat de terminal (chat.py) a persona, a base de conhecimento, o
cache semântico, a conexão com o servidor MCP e as regras do histórico e do
cache. O que muda é a apresentação: a resposta chega em streaming, cada
ferramenta MCP executada aparece como uma etapa que pode ser aberta, o
raciocínio do modelo fica num bloco recolhido e as leituras de sensores viram
gráficos.

Execução (com o Ollama e o ferramentas.py no ar):
    chainlit run app.py --port 8001
"""
import asyncio
import json
from contextlib import AsyncExitStack, suppress

import chainlit as cl
from chainlit.utils import utc_now

from cache import buscar_cache, gravar_cache, iniciar_cache
from chat import (
    CACHE, LIMITE_RODADAS_FERRAMENTAS, MODELO, MODELO_CACHE, NOME_CACHE, RESPOSTA_RECUSA,
    URL_FERRAMENTAS, carregar_conhecimento, conectar_ferramentas, extrair_texto_execucao,
    iniciar_persona_assistente, registrar_historico, servidor_disponivel,
)
from graficos import desembrulhar_resultado, extrair_leituras, gerar_grafico
from llm import URL_OLLAMA, iniciar_ollama_async, transmitir_resposta

LIMITE_GRAFICOS = 3
MARCA_CONTINGENCIA = "contingência"

AVISO_MCP = (
    f"Servidor de ferramentas MCP indisponível em {URL_FERRAMENTAS}: o PlantaBot está respondendo "
    "sem consultar sensores, alarmes e ordens de serviço. Execute 'python ferramentas.py' e abra uma nova conversa."
)
AVISO_MCP_QUEDA = (
    "O servidor de ferramentas MCP parou de responder: o PlantaBot vai terminar a resposta "
    "sem novas consultas. Execute 'python ferramentas.py' e abra uma nova conversa."
)
AVISO_CONTINGENCIA = (
    "**Dados simulados.** Os microsserviços da planta estão indisponíveis e as ferramentas "
    "devolveram dados de contingência, não o estado atual da planta."
)
AVISO_OLLAMA = (
    f"Não foi possível conectar ao Ollama em {URL_OLLAMA}. Inicie o servidor "
    f"(`ollama serve`), confirme que o modelo `{MODELO}` está baixado e abra uma nova conversa."
)


class ConexaoMCP:
    """Uma conexão com o servidor MCP compartilhada por todas as conversas.

    O cliente MCP precisa ser aberto e fechado pela mesma tarefa do asyncio, e o
    Chainlit executa cada evento numa tarefa diferente. Por isso a conexão vive
    numa tarefa própria, que a mantém aberta enquanto o servidor responder. Se
    ela cair, a próxima conversa tenta conectar de novo.
    """

    def __init__(self):
        self.mapa, self.ferramentas = {}, []
        self._tarefa = None

    @property
    def conectada(self):
        return bool(self.ferramentas) and self._tarefa is not None and not self._tarefa.done()

    async def conectar(self):
        if self.conectada:
            # a conexão só percebe que o servidor caiu na chamada seguinte; o teste
            # de porta descobre isso antes, sem gastar uma chamada de ferramenta
            if await servidor_disponivel(URL_FERRAMENTAS):
                return
            await self.desconectar()
        pronta = asyncio.Event()

        async def manter():
            try:
                async with AsyncExitStack() as contexto:
                    self.mapa, self.ferramentas = await conectar_ferramentas(contexto)
                    pronta.set()
                    if self.ferramentas:
                        await asyncio.Event().wait()
            except Exception as e:
                print(f"conexão com o servidor MCP encerrada: {e}")
            finally:
                self.mapa, self.ferramentas = {}, []
                pronta.set()

        self._tarefa = asyncio.create_task(manter())
        await pronta.wait()

    async def desconectar(self):
        if self._tarefa is not None and not self._tarefa.done():
            self._tarefa.cancel()
            with suppress(asyncio.CancelledError):
                await self._tarefa
        self.mapa, self.ferramentas = {}, []


class Recursos:
    """O que é caro de carregar fica pronto uma vez só e é compartilhado entre as conversas."""

    def __init__(self):
        self.trava = asyncio.Lock()
        self.persona = None
        self.modelo_cache = self.colecao_cache = None
        self.ollama = None
        self.mcp = ConexaoMCP()

    async def preparar(self):
        async with self.trava:
            if self.persona is None:
                carregado, conhecimento = carregar_conhecimento()
                if carregado:
                    self.persona = iniciar_persona_assistente(conhecimento)

            if self.colecao_cache is None:
                # o modelo de embeddings leva alguns segundos para carregar; numa
                # thread à parte, ele não trava a interface enquanto isso
                iniciado, modelo, colecao = await cl.make_async(iniciar_cache)(MODELO_CACHE, CACHE, NOME_CACHE)
                if iniciado:
                    self.modelo_cache, self.colecao_cache = modelo, colecao

            if self.ollama is None:
                iniciado, ollama = await iniciar_ollama_async()
                if iniciado:
                    self.ollama = ollama

            await self.mcp.conectar()


recursos = Recursos()


@cl.set_starters
async def perguntas_iniciais(usuario = None, idioma = None):
    return [
        cl.Starter(label = "Resumo dos alarmes", message = "Faça um resumo dos alarmes da planta por equipamento e severidade."),
        cl.Starter(label = "Alarmes críticos", message = "Quais alarmes de severidade crítica existem na planta?"),
        cl.Starter(label = "Diagnóstico da Caldeira 1", message = "Faça o diagnóstico da Caldeira 1."),
        cl.Starter(label = "Leituras do Compressor 3", message = "Mostre as leituras dos sensores do Compressor 3."),
        cl.Starter(label = "Ordens de serviço abertas", message = "Quais ordens de serviço estão abertas?"),
        cl.Starter(label = "O que é setpoint?", message = "O que é um setpoint em automação e supervisão industrial?"),
    ]


@cl.on_chat_start
async def iniciar_conversa():
    cl.user_session.set("historico", [])
    await recursos.preparar()

    # os avisos de início vão como toast: uma mensagem na conversa esconderia as perguntas iniciais
    if recursos.ollama is None:
        await cl.context.emitter.send_toast(AVISO_OLLAMA.replace("`", ""), "error")
    elif not recursos.mcp.conectada:
        await cl.context.emitter.send_toast(AVISO_MCP, "warning")


def formatar_json(texto):
    try:
        return json.dumps(desembrulhar_resultado(json.loads(texto)), ensure_ascii = False, indent = 2), "json"
    except (TypeError, json.JSONDecodeError):
        return texto, None


async def executar_ferramenta(chamada):
    """Executa uma ferramenta MCP e a mostra na conversa como uma etapa que pode ser aberta."""
    nome = chamada["nome"]
    try:
        argumentos = json.loads(chamada["argumentos"]) if chamada["argumentos"] else {}
    except json.JSONDecodeError:
        argumentos = {}

    async with cl.Step(name = nome, type = "tool") as etapa:
        etapa.input = argumentos
        info = recursos.mcp.mapa.get(nome)
        if info is None:
            resultado = f"ferramenta '{nome}' não encontrada"
            etapa.is_error = True
        else:
            try:
                execucao = await info["conexao"].call_tool(nome, arguments = argumentos or {})
                resultado = extrair_texto_execucao(execucao)
            except Exception as e:
                resultado = f"erro executando a ferramenta '{nome}': {e}"
                etapa.is_error = True
                if not await servidor_disponivel(URL_FERRAMENTAS):
                    await recursos.mcp.desconectar()
        etapa.output, etapa.language = formatar_json(resultado)

    return resultado


def titulo_grafico(nome_ferramenta, leituras):
    equipamentos = {l.get("equipamento_nome") for l in leituras if l.get("equipamento_nome")}
    if len(equipamentos) == 1:
        return f"Leituras de {equipamentos.pop()}"
    if nome_ferramenta == "ultima_leitura":
        return "Última leitura de cada sensor da planta"
    return "Leituras dos sensores"


def montar_rodape(origem, ferramentas_usadas):
    partes = [origem]
    if ferramentas_usadas:
        partes.append(f"🛠️ {ferramentas_usadas} consulta(s) às ferramentas MCP")
    if not recursos.mcp.conectada:
        partes.append("⚠️ sem ferramentas MCP")
    # o Chainlit não interpreta HTML nas mensagens: o rodapé é Markdown puro
    return "\n\n---\n*" + " · ".join(partes) + "*"


async def responder_com_llm(mensagens):
    """Executa o ciclo pergunta → ferramentas → resposta, mostrando cada parte na interface.

    Retorna (sucesso, texto, ferramentas_usadas, mensagem, graficos).
    """
    mensagem = cl.Message(content = "")
    raciocinio = None
    ferramentas_usadas, contingencia, graficos = 0, False, []

    async def ao_pensar(trecho):
        nonlocal raciocinio
        if raciocinio is None:
            # criada fora de um 'async with', a etapa não herda o pai sozinha; sem ele,
            # a interface a desenha depois da resposta, e não dentro da pergunta
            etapa_atual = cl.context.current_step
            raciocinio = cl.Step(
                name = "Raciocínio", type = "llm", show_input = False,
                parent_id = etapa_atual.id if etapa_atual else None
            )
            raciocinio.start = utc_now()
        await raciocinio.stream_token(trecho)

    async def ao_escrever(trecho):
        # a interface ordena pela hora de criação: a resposta é datada quando começa
        # a ser escrita, para ficar depois das etapas de raciocínio e de ferramenta
        if not mensagem.streaming:
            mensagem.created_at = utc_now()
        await mensagem.stream_token(trecho)

    async def encerrar_raciocinio():
        nonlocal raciocinio
        if raciocinio is not None:
            # update, e não send: o send reenvia a etapa como nova e ela vai para o fim da conversa
            raciocinio.end = utc_now()
            await raciocinio.update()
            raciocinio = None

    avisou_queda = False

    for _ in range(LIMITE_RODADAS_FERRAMENTAS):
        # recalculada a cada rodada: se o servidor MCP cair no meio da resposta,
        # o modelo para de receber as ferramentas e responde com o que já tem
        ferramentas = recursos.mcp.ferramentas if recursos.mcp.conectada else None
        if ferramentas is None and ferramentas_usadas and not avisou_queda:
            avisou_queda = True
            await cl.context.emitter.send_toast(AVISO_MCP_QUEDA, "warning")

        sucesso, texto, chamadas = await transmitir_resposta(
            recursos.ollama, mensagens, ferramentas = ferramentas, modelo = MODELO,
            ao_pensar = ao_pensar, ao_escrever = ao_escrever
        )
        await encerrar_raciocinio()
        if not sucesso:
            return False, None, ferramentas_usadas, mensagem, graficos
        if not chamadas:
            return True, texto, ferramentas_usadas, mensagem, graficos

        # o modelo pediu ferramentas: o texto que tenha escrito até aqui não é a resposta final
        if mensagem.streaming:
            await mensagem.remove()
            mensagem = cl.Message(content = "")

        mensagens.append({
            "role": "assistant",
            "content": texto,
            "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["nome"], "arguments": c["argumentos"] or "{}"}, **c["extras"]}
                for c in chamadas
            ]
        })
        for chamada in chamadas:
            resultado = await executar_ferramenta(chamada)
            ferramentas_usadas += 1

            # o aviso não depende do LLM: se a ferramenta usou dados de contingência,
            # o operador fica sabendo antes mesmo de a resposta começar
            if MARCA_CONTINGENCIA in resultado and not contingencia:
                contingencia = True
                await cl.Message(content = f"⚠️ {AVISO_CONTINGENCIA}", author = "Aviso").send()

            leituras = extrair_leituras(chamada["nome"], resultado)
            if leituras and len(graficos) < LIMITE_GRAFICOS:
                figura = gerar_grafico(leituras, titulo_grafico(chamada["nome"], leituras))
                if figura is not None:
                    graficos.append(figura)

            mensagens.append({"role": "tool", "tool_call_id": chamada["id"], "name": chamada["nome"], "content": resultado})

    # o modelo esgotou as rodadas pedindo ferramentas: exige a resposta final só com o que já foi coletado
    sucesso, texto, _ = await transmitir_resposta(
        recursos.ollama, mensagens, modelo = MODELO, ao_pensar = ao_pensar, ao_escrever = ao_escrever
    )
    await encerrar_raciocinio()
    return sucesso, texto, ferramentas_usadas, mensagem, graficos


@cl.on_message
async def responder(mensagem_usuario: cl.Message):
    pergunta = mensagem_usuario.content.strip()
    if not pergunta:
        return
    historico = cl.user_session.get("historico")

    if recursos.ollama is None:
        # o Ollama pode ter sido iniciado depois da abertura da conversa
        await recursos.preparar()
        if recursos.ollama is None:
            await cl.ErrorMessage(content = AVISO_OLLAMA).send()
            return

    if recursos.colecao_cache is not None:
        encontrada, resposta = await cl.make_async(buscar_cache)(pergunta, recursos.modelo_cache, recursos.colecao_cache)
        if encontrada:
            await cl.Message(content = resposta + montar_rodape("💾 recuperada do cache", 0)).send()
            registrar_historico(historico, pergunta, resposta)
            return

    mensagens = recursos.persona + historico + [{"role": "user", "content": pergunta}]
    sucesso, resposta, ferramentas_usadas, mensagem, graficos = await responder_com_llm(mensagens)

    if not (sucesso and resposta):
        if mensagem.streaming:
            await mensagem.remove()
        await cl.Message(
            content = "🤖 não sei responder esta pergunta, pergunte outra coisa sobre supervisão e manutenção da planta industrial"
        ).send()
        return

    mensagem.content = resposta + montar_rodape(f"🤖 resposta do llm ({MODELO})", ferramentas_usadas)
    mensagem.elements = [
        cl.Plotly(name = f"grafico_{indice}", figure = figura, display = "inline")
        for indice, figura in enumerate(graficos, start = 1)
    ]
    await mensagem.send()

    registrar_historico(historico, pergunta, resposta)
    # respostas montadas com ferramentas refletem o estado da planta naquele instante
    # e recusas não são conhecimento: nenhuma das duas vai para o cache
    if ferramentas_usadas == 0 and RESPOSTA_RECUSA not in resposta.lower() and recursos.colecao_cache is not None:
        await cl.make_async(gravar_cache)(pergunta, resposta, recursos.modelo_cache, recursos.colecao_cache)
