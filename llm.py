import re
from openai import AsyncOpenAI, OpenAI

MODELO = "qwen3:4b"
URL_OLLAMA = "http://localhost:11434/v1/"

def iniciar_ollama():
    iniciado, ollama = False, None

    try:
        ollama = OpenAI(
            base_url = URL_OLLAMA,
            api_key = "ollama"
        )
        # criar o cliente não abre conexão: a listagem de modelos confirma
        # que o servidor do Ollama está realmente no ar
        ollama.models.list()

        iniciado = True
    except Exception as e:
        print(f"não foi possível conectar ao Ollama em {URL_OLLAMA}: {e}")

    return iniciado, ollama

def limpar_pensamento(texto):
    if not texto:
        return texto
    texto_limpo = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()
    return texto_limpo if texto_limpo else texto.strip()

def obter_resposta(ollama, mensagens, modelo = MODELO):
    sucesso, resposta = False, None

    try:
        conclusao = ollama.chat.completions.create(
            messages = mensagens,
            model = modelo,
            temperature = 0.1
        )
        resposta = limpar_pensamento(conclusao.choices[0].message.content)

        sucesso = True
    except Exception as e:
        print(f"ocorreu um erro ao obter resposta: {e}")

    return sucesso, resposta

def obter_resposta_com_ferramentas(ollama, mensagens, ferramentas = None, modelo = MODELO):
    sucesso, mensagem_resposta = False, None

    try:
        parametros = {
            "messages": mensagens,
            "model": modelo,
            "temperature": 0.1
        }
        if ferramentas:
            parametros["tools"] = ferramentas

        conclusao = ollama.chat.completions.create(**parametros)
        mensagem_resposta = conclusao.choices[0].message
        sucesso = True
    except Exception as e:
        print(f"ocorreu um erro ao obter resposta com ferramentas: {e}")

    return sucesso, mensagem_resposta

# --- versão assíncrona e em streaming, usada pela interface web (app.py) ---

INICIO_PENSAMENTO, FIM_PENSAMENTO = "<think>", "</think>"


async def iniciar_ollama_async():
    iniciado, ollama = False, None

    try:
        ollama = AsyncOpenAI(
            base_url = URL_OLLAMA,
            api_key = "ollama"
        )
        await ollama.models.list()

        iniciado = True
    except Exception as e:
        print(f"não foi possível conectar ao Ollama em {URL_OLLAMA}: {e}")

    return iniciado, ollama


class SeparadorPensamento:
    """Separa, durante o streaming, o raciocínio entre <think> e </think> do texto da resposta.

    As marcas podem chegar quebradas entre dois pedaços (por exemplo '<thi' e 'nk>'),
    então o final de cada pedaço que ainda pode ser o começo de uma marca fica retido
    até o pedaço seguinte.
    """

    def __init__(self):
        self.pensando = False
        self.pendente = ""

    def alimentar(self, texto):
        self.pendente += texto
        trechos = []

        while self.pendente:
            marca = FIM_PENSAMENTO if self.pensando else INICIO_PENSAMENTO
            tipo = "pensamento" if self.pensando else "resposta"
            posicao = self.pendente.find(marca)

            if posicao >= 0:
                trechos.append((tipo, self.pendente[:posicao]))
                self.pendente = self.pendente[posicao + len(marca):]
                self.pensando = not self.pensando
                continue

            retido = 0
            for tamanho in range(min(len(marca) - 1, len(self.pendente)), 0, -1):
                if marca.startswith(self.pendente[-tamanho:]):
                    retido = tamanho
                    break
            trechos.append((tipo, self.pendente[:len(self.pendente) - retido]))
            self.pendente = self.pendente[len(self.pendente) - retido:]
            break

        return [(tipo, trecho) for tipo, trecho in trechos if trecho]

    def finalizar(self):
        tipo = "pensamento" if self.pensando else "resposta"
        trecho, self.pendente = self.pendente, ""
        return [(tipo, trecho)] if trecho else []


async def transmitir_resposta(ollama, mensagens, ferramentas = None, modelo = MODELO, ao_pensar = None, ao_escrever = None):
    """Pede a resposta ao Ollama em streaming.

    O raciocínio vai para ao_pensar e o texto da resposta para ao_escrever, à medida
    que chegam. Retorna (sucesso, texto, chamadas), em que chamadas é a lista de
    ferramentas pedidas pelo modelo, cada uma como {"id", "nome", "argumentos"}.
    """
    sucesso, texto, chamadas = False, "", {}
    separador = SeparadorPensamento()

    async def entregar(trechos):
        nonlocal texto
        for tipo, trecho in trechos:
            if tipo == "pensamento":
                if ao_pensar:
                    await ao_pensar(trecho)
            else:
                texto += trecho
                if ao_escrever:
                    await ao_escrever(trecho)

    try:
        parametros = {
            "messages": mensagens,
            "model": modelo,
            "temperature": 0.1,
            "stream": True
        }
        if ferramentas:
            parametros["tools"] = ferramentas

        fluxo = await ollama.chat.completions.create(**parametros)
        async for pedaco in fluxo:
            if not pedaco.choices:
                continue
            delta = pedaco.choices[0].delta

            # versões recentes do Ollama mandam o raciocínio num campo próprio,
            # em vez de deixá-lo entre <think> e </think> no texto
            raciocinio = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
            if raciocinio and ao_pensar:
                await ao_pensar(raciocinio)

            if delta.content:
                await entregar(separador.alimentar(delta.content))

            # cada chamada de ferramenta pode chegar em vários pedaços, ligados pelo índice
            for parte in delta.tool_calls or []:
                indice = parte.index if parte.index is not None else len(chamadas)
                chamada = chamadas.setdefault(indice, {"id": None, "nome": "", "argumentos": "", "extras": {}})
                # alguns servidores compatíveis com a API da OpenAI anexam à chamada dados
                # próprios que precisam voltar na rodada seguinte (o Gemini, por exemplo,
                # exige de volta a assinatura do raciocínio); eles são guardados como vieram
                chamada["extras"].update(parte.model_extra or {})
                if parte.id:
                    chamada["id"] = parte.id
                if parte.function and parte.function.name:
                    chamada["nome"] += parte.function.name
                if parte.function and parte.function.arguments:
                    chamada["argumentos"] += parte.function.arguments

        await entregar(separador.finalizar())
        sucesso = True
    except Exception as e:
        print(f"ocorreu um erro ao obter resposta em streaming: {e}")

    lista_chamadas = []
    for indice, chamada in sorted(chamadas.items()):
        chamada["id"] = chamada["id"] or f"chamada_{indice}"
        lista_chamadas.append(chamada)

    return sucesso, texto.strip(), lista_chamadas


def executar():
    iniciado, ollama = iniciar_ollama()
    if not iniciado:
        return
    print("ollama iniciado")

    mensagens = [
        {
            "role": "system",
            "content": "Elabore uma resposta curta para uma saudação. Na sua resposta, você deve se identificar como um sistema especialista dedicado ao diagnóstico operacional e supervisão de planta industrial"
        },
        {
            "role": "system",
            "content": "O seu nome é PlantaBot. Sempre se identifique com esse nome durante saudações"
        },
        {
            "role": "user",
            "content": "olá, tudo bem?"
        }
    ]

    sucesso, resposta = obter_resposta(ollama, mensagens)
    if sucesso:
        print(f"resposta do llm: {resposta}")
    else:
        print("não foi possível obter uma resposta do llm")

if __name__ == "__main__":
    executar()
