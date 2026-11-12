import unittest

# importações explícitas: 'from chat import *' seguido de 'from llm import *'
# trocava silenciosamente o MODELO do assistente pelo do módulo llm
from chat import MODELO, carregar_conhecimento, iniciar_persona_assistente
from llm import iniciar_ollama, obter_resposta


class TesteChat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        iniciado, cls.ollama = iniciar_ollama()
        assert iniciado, "Ollama indisponível"
        print("ollama iniciado")

        carregado, conhecimento = carregar_conhecimento()
        assert carregado, "base de conhecimento indisponível"
        cls.assistente = iniciar_persona_assistente(conhecimento)
        print(f"persona do assistente carregada (modelo {MODELO})")

    def perguntar(self, pergunta):
        sucesso, resposta = obter_resposta(self.ollama, self.assistente + [
            {
                "role": "user",
                "content": pergunta
            }
        ], modelo=MODELO)
        self.assertTrue(sucesso)

        print(f"resposta da IA: {resposta}")
        return resposta.lower()

    def testar_resposta_correta(self):
        resposta = self.perguntar("Quais grandezas físicas são monitoradas pelos sensores da planta?")

        for termo in ["temperatura", "pressão", "vibração"]:
            self.assertIn(termo, resposta)

    def testar_pergunta_proibida(self):
        resposta = self.perguntar("Quem descobriu o Brasil?")

        for termo in ["não", "posso", "responder"]:
            self.assertIn(termo, resposta)


if __name__ == "__main__":
    unittest.main()
