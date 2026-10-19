from chat import *
from llm import *

MODELO_ASSISTENTE = "qwen2.5:1.5b"
MODELO_JULGAMENTO = "qwen3:4b"
BASE_CONHECIMENTO_JULGAMENTO = DIRETORIO_BASE / "conhecimento" / "planta_menor.json"

def iniciar_persona_julgamento(conhecimento):
    persona = [
        {
            "role": "system",
            "content": "Você é um especialista, perito, em supervisão operacional, instrumentação e manutenção de planta industrial"
        },
        {
            "role": "system",
            "content": "Sua função é avaliar se uma determinada resposta responde adequadamente uma pergunta sobre supervisão, diagnóstico de sensores, alarmes e manutenção da planta industrial"
        }
    ]

    for mensagem, resposta in conhecimento:
        persona.append({
            "role": "system",
            "content": f"Caso a pergunta seja '{mensagem}' ou algo parecido, você deve verificar se a resposta é '{resposta}' ou algo parecido"
        })

    persona.append(
        {
            "role": "system",
            "content": "A sua resposta deve conter APENAS uma string que informe, 'ATENDE', se a resposta responde a pergunta e 'NÃO ATENDE' se a resposta não responde a pergunta. Não é necessário explicar o seu julgamento."
        }
    )

    return persona

def avaliar_alucinacoes(ollama, julgador):
    alucinacoes = [
        {
            "pergunta": "O que é um Sistema Supervisório de Planta Industrial?",
            "resposta": "É um tipo de pássaro que viaja para o sul no inverno"
        },
        {
            "pergunta": "O que é um setpoint em automação e supervisão industrial?",
            "resposta": "É um tipo de comida que serve para alimentar pássaros"
        }
    ]

    for alucinacao in alucinacoes:
        pergunta = alucinacao["pergunta"]
        resposta = alucinacao["resposta"]

        print(f"julgando a resposta '{resposta}' para a pergunta '{pergunta}'")

        sucesso, julgamento = obter_resposta(ollama, julgador + [
            {
                "role": "user",
                "content": f"pergunta '{pergunta}', resposta '{resposta}'"
            }
        ], modelo = MODELO_JULGAMENTO)
        assert(sucesso == True)

        print(f"resposta do julgador: {julgamento}")
        assert("NÃO ATENDE" in julgamento)

        print("👍👍 a alucinação foi julgada insatisfatória 👍👍")

def julgar_assistente(ollama, conhecimento, assistente, julgador):
    for pergunta, _ in conhecimento:
        sucesso, resposta = obter_resposta(ollama, assistente + [
            {
                "role": "user",
                "content": pergunta
            }
        ], modelo = MODELO_ASSISTENTE)
        assert(sucesso == True)

        print(f"julgando a resposta '{resposta}' para a pergunta '{pergunta}'")

        sucesso, julgamento = obter_resposta(ollama, julgador + [
            {
                "role": "user",
                "content": f"pergunta '{pergunta}', resposta '{resposta}'"
            }
        ], modelo = MODELO_JULGAMENTO)
        assert(sucesso == True)

        print(f"resposta do julgador: {julgamento}")
        assert("NÃO ATENDE" not in julgamento)

        print("👍👍 a resposta do assistente foi julgada satisfatória 👍👍")


if __name__ == "__main__":
    iniciado, ollama = iniciar_ollama()
    assert(iniciado == True)

    carregado, conhecimento = carregar_conhecimento(BASE_CONHECIMENTO_JULGAMENTO)
    assert(carregado == True)

    julgador = iniciar_persona_julgamento(conhecimento)
    assistente = iniciar_persona_assistente(conhecimento)

    avaliar_alucinacoes(ollama, julgador)
    julgar_assistente(ollama, conhecimento, assistente, julgador)

    print("👍👍 julgamento finalizando com sucesso! 👍👍")
