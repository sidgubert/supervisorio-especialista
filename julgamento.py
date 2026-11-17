import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from chat import DIRETORIO_BASE, MODELO, carregar_conhecimento, iniciar_persona_assistente
from llm import iniciar_ollama, obter_resposta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# a chave da API do Gemini (GOOGLE_API_KEY) fica no arquivo .env da raiz do projeto
load_dotenv(DIRETORIO_BASE / ".env")

# o assistente julgado é o mesmo modelo local usado no chat (Ollama); o julgador
# é o Gemini, do Google, e pode ser trocado sem editar o código: defina PLANTABOT_MODELO_JULGADOR
MODELO_ASSISTENTE = MODELO
MODELO_JULGAMENTO = os.environ.get("PLANTABOT_MODELO_JULGADOR", "gemini-3.6-flash")
BASE_CONHECIMENTO_JULGAMENTO = DIRETORIO_BASE / "conhecimento" / "planta_menor.json"

VEREDITO_APROVADO = "ATENDE"
VEREDITO_REPROVADO = "NÃO ATENDE"

# respostas erradas, mas com aparência técnica, usadas para conferir se o julgador
# realmente reprova o que contradiz a base de conhecimento da planta
ALUCINACOES = [
    {
        "pergunta": "Quais grandezas físicas são monitoradas pelos sensores da planta?",
        "resposta": "Os sensores monitoram apenas a umidade relativa do ar e a velocidade do vento em torno de cada equipamento."
    },
    {
        "pergunta": "O que é um setpoint em automação e supervisão industrial?",
        "resposta": "É o nome dado ao técnico responsável por executar a ordem de serviço de um equipamento."
    },
    {
        "pergunta": "Quais são os equipamentos monitorados na planta industrial PlantaView?",
        "resposta": "A planta possui apenas três equipamentos instrumentados: duas turbinas eólicas e um forno de padaria."
    }
]


def iniciar_gemini():
    iniciado, gemini = False, None

    try:
        gemini = genai.Client(api_key = os.environ["GOOGLE_API_KEY"])
        # criar o cliente não valida nada: consultar o modelo confirma que a
        # chave é aceita e que o nome do modelo julgador existe
        gemini.models.get(model = MODELO_JULGAMENTO)

        iniciado = True
    except KeyError:
        print("GOOGLE_API_KEY não definida: copie .env.example para .env e informe a sua chave")
    except Exception as e:
        print(f"não foi possível conectar ao Gemini com o modelo {MODELO_JULGAMENTO}: {e}")

    return iniciado, gemini


def iniciar_persona_julgamento(conhecimento):
    # no formato de requisição do Gemini, as regras do julgador não fazem parte
    # da conversa: elas são enviadas à parte, como instrução de sistema
    gabarito = "\n".join(
        f"- Caso a pergunta seja '{mensagem}' ou algo parecido, você deve verificar se a resposta é '{resposta}' ou algo parecido"
        for mensagem, resposta in conhecimento
    )

    return (
        "Você é um especialista, perito, em supervisão operacional, instrumentação e manutenção de planta industrial.\n"
        "Sua função é avaliar se uma determinada resposta responde adequadamente uma pergunta sobre supervisão, "
        "diagnóstico de sensores, alarmes e manutenção da planta industrial.\n"
        "Gabarito:\n"
        f"{gabarito}\n"
        "Uma resposta com o mesmo sentido do gabarito, ainda que mais detalhada ou com outras palavras, responde a pergunta. "
        "Uma resposta que contradiz o gabarito não responde a pergunta.\n"
        f"A sua resposta deve conter APENAS uma string que informe, '{VEREDITO_APROVADO}', se a resposta responde a pergunta "
        f"e '{VEREDITO_REPROVADO}' se a resposta não responde a pergunta. Não é necessário explicar o seu julgamento."
    )


def obter_julgamento(gemini, persona_julgador, pergunta, resposta):
    sucesso, julgamento = False, None

    try:
        # requisição no formato do Gemini: 'contents' leva o par a ser julgado e
        # 'system_instruction' leva a persona do julgador com o gabarito; a
        # temperatura fica no padrão, como o Google recomenda para os modelos Gemini 3.
        # O julgador não usa ferramentas, então a chamada automática de funções
        # (ligada por padrão no google-genai) é desligada
        conclusao = gemini.models.generate_content(
            model = MODELO_JULGAMENTO,
            contents = f"pergunta '{pergunta}', resposta '{resposta}'",
            config = types.GenerateContentConfig(
                system_instruction = persona_julgador,
                automatic_function_calling = types.AutomaticFunctionCallingConfig(disable = True)
            )
        )
        julgamento = conclusao.text

        sucesso = True
    except Exception as e:
        print(f"ocorreu um erro ao obter o julgamento do Gemini: {e}")

    return sucesso, julgamento


def resumir(texto, limite = 95):
    """Encurta o texto só para exibição no terminal; o julgador sempre recebe a resposta completa."""
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= limite else texto[:limite].rstrip() + "..."


def interpretar_veredito(julgamento):
    """Devolve True (atende), False (não atende) ou None quando o julgador não deu um veredito reconhecível."""
    texto = (julgamento or "").upper()

    if VEREDITO_REPROVADO in texto or "NAO ATENDE" in texto:
        return False
    if VEREDITO_APROVADO in texto:
        return True
    return None


def julgar(gemini, persona_julgador, pergunta, resposta):
    sucesso, julgamento = obter_julgamento(gemini, persona_julgador, pergunta, resposta)
    assert sucesso, "o julgador não respondeu"

    return interpretar_veredito(julgamento), resumir(julgamento, 40)


def avaliar_alucinacoes(gemini, persona_julgador):
    """Etapa 1: o julgador precisa reprovar respostas deliberadamente erradas."""
    acertos = 0

    for indice, alucinacao in enumerate(ALUCINACOES, start = 1):
        pergunta, resposta = alucinacao["pergunta"], alucinacao["resposta"]

        print(f"[alucinação {indice}/{len(ALUCINACOES)}] pergunta: '{pergunta}'")
        print(f"   resposta errada: '{resposta}'")

        veredito, julgamento = julgar(gemini, persona_julgador, pergunta, resposta)
        if veredito is False:
            acertos += 1
            print(f"   julgador: {julgamento} 👍 a alucinação foi julgada insatisfatória")
        else:
            print(f"   julgador: {julgamento} 👎 o julgador NÃO reprovou a alucinação")

    return acertos, len(ALUCINACOES)


def julgar_assistente(ollama, gemini, conhecimento, assistente, persona_julgador):
    """Etapa 2: o assistente responde pelo Ollama e o julgador avalia pelo Gemini."""
    acertos = 0

    for indice, (pergunta, _) in enumerate(conhecimento, start = 1):
        sucesso, resposta = obter_resposta(ollama, assistente + [
            {
                "role": "user",
                "content": pergunta
            }
        ], modelo = MODELO_ASSISTENTE)
        assert sucesso, "o assistente não respondeu"

        print(f"[assistente {indice}/{len(conhecimento)}] pergunta: '{pergunta}'")
        print(f"   resposta do assistente: '{resumir(resposta)}'")

        veredito, julgamento = julgar(gemini, persona_julgador, pergunta, resposta)
        if veredito is True:
            acertos += 1
            print(f"   julgador: {julgamento} 👍 a resposta do assistente foi julgada satisfatória")
        else:
            print(f"   julgador: {julgamento} 👎 a resposta do assistente NÃO foi julgada satisfatória")

    return acertos, len(conhecimento)


def executar():
    iniciado, ollama = iniciar_ollama()
    assert iniciado, "Ollama indisponível"

    iniciado, gemini = iniciar_gemini()
    assert iniciado, "Gemini indisponível"

    carregado, conhecimento = carregar_conhecimento(BASE_CONHECIMENTO_JULGAMENTO)
    assert carregado and len(conhecimento) > 0, "base de conhecimento do julgamento indisponível"

    persona_julgador = iniciar_persona_julgamento(conhecimento)
    assistente = iniciar_persona_assistente(conhecimento)

    print(f"julgamento LLM-as-a-Judge | assistente: {MODELO_ASSISTENTE} (Ollama) | julgador: {MODELO_JULGAMENTO} (Gemini)")

    reprovadas, total_alucinacoes = avaliar_alucinacoes(gemini, persona_julgador)
    aprovadas, total_respostas = julgar_assistente(ollama, gemini, conhecimento, assistente, persona_julgador)

    print(f"placar: {reprovadas}/{total_alucinacoes} alucinações reprovadas, {aprovadas}/{total_respostas} respostas do assistente aprovadas")

    assert reprovadas == total_alucinacoes, "o julgador deixou passar alucinações"
    assert aprovadas == total_respostas, "há respostas do assistente reprovadas"

    print("👍👍 julgamento finalizado com sucesso! 👍👍")


if __name__ == "__main__":
    executar()
