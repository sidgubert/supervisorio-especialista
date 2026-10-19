import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Carrega o .env da pasta mcp
load_dotenv(dotenv_path=r"c:\Users\sidgubert\Documents\dev\Desenvolvimento Orientado a Serviços\Trabalho_MCP_Anti\mcp\.env")

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERRO: GOOGLE_API_KEY não encontrada no arquivo .env")
    exit(1)

print(f"SUCESSO: GOOGLE_API_KEY carregada com sucesso (tamanho: {len(api_key)} caracteres).")
print(f"Primeiros caracteres da chave: {api_key[:5]}...")

try:
    print("Testando conexao com o Google Gemini API...")
    # Tenta criar o cliente e fazer uma chamada simples
    client = genai.Client(api_key=api_key)
    # Apenas um modelo barato para testar a chave
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents='Teste de conexão. Responda apenas "OK".'
    )
    print("SUCESSO: A API Key e valida e a conexao foi estabelecida!")
    print(f"Resposta do Gemini: {response.text}")

except errors.APIError as e:
    print("\nERRO NA API DO GOOGLE:")
    print(f"Status Code: {e.code}")
    print(f"Mensagem: {e.message}")
    print("Isso geralmente significa que a chave esta incorreta ou sem permissao.")
except Exception as e:
    print(f"\nERRO INESPERADO: {str(e)}")
