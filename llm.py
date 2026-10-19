import re
from openai import OpenAI

MODELO = "qwen3:4b"
URL_OLLAMA = "http://localhost:11434/v1/"

def iniciar_ollama():
    iniciado, ollama = False, None

    try:
        ollama = OpenAI(
            base_url = URL_OLLAMA,
            api_key = "ollama"
        )

        iniciado = True
    except Exception as e:
        print(f"ocorreu um problema iniciando o llm: {e}")

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

    sucesso, resposta = obter_resposta(ollama, mensagens, modelo = "qwen2.5:1.5b")
    if sucesso:
        print(f"resposta do llm: {resposta}")
    else:
        print("não foi possível obter uma resposta do llm")

if __name__ == "__main__":
    executar()
