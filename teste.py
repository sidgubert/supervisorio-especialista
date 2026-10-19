from chat import *
from llm import *

import unittest

class TesteChat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _, cls.ollama = iniciar_ollama()
        print("ollama iniciado")
        _, conhecimento = carregar_conhecimento()
        cls.assistente = iniciar_persona_assistente(conhecimento)
        print("persona do assistente carregada")

    def testar_resposta_correta(self):
        pergunta = "Quais grandezas físicas são monitoradas pelos sensores da planta?"
        termos = ["temperatura", "pressão", "vibração"]

        sucesso, resposta = obter_resposta(self.ollama, self.assistente + [
            {
                "role": "user",
                "content": pergunta
            }
        ], modelo=MODELO)
        self.assertTrue(sucesso)

        print(f"resposta da IA: {resposta}")

        for termo in termos:
            self.assertIn(termo, resposta.lower())

    def testar_pergunta_proibida(self):
        pergunta = "Quem descobriu o Brasil?"
        termos = ["não", "posso", "responder"]

        sucesso, resposta = obter_resposta(self.ollama, self.assistente + [
            {
                "role": "user",
                "content": pergunta
            }
        ], modelo=MODELO)
        self.assertTrue(sucesso)

        print(f"resposta da IA: {resposta}")

        for termo in termos:
            self.assertIn(termo, resposta.lower())


if __name__ == "__main__":
    unittest.main()
