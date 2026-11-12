from mcp.server.mcpserver import MCPServer
import urllib.request as requisicao

NOME = "sensores"
mcp = MCPServer(NOME)

URL_BASE = "http://sensores:5000"

def acessar(url):
    sucesso, conteudo, erro = False, None, None
    try:
        resposta = requisicao.urlopen(url)
        if resposta.code == 200:
            conteudo = resposta.read().decode("utf-8")
            sucesso = True
    except Exception as e:
        erro = str(e)
        print(f"ocorreu um erro acessando: {url}, erro: {erro}")
    return sucesso, conteudo, erro

@mcp.tool(name="leituras_por_equipamento", title="Leituras por Equipamento", description="retorna as leituras de sensores de um equipamento identificado pelo seu id. Equipamentos: 1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1")
def leituras_por_equipamento(equipamento_id: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/leituras/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="leituras_por_grandeza", title="Leituras por Grandeza", description="retorna leituras de um equipamento filtradas por grandeza (temperatura, pressao ou vibracao)")
def leituras_por_grandeza(equipamento_id: str, grandeza: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/leituras/equipamento/{equipamento_id}/grandeza/{grandeza}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="ultima_leitura", title="Ultima Leitura", description="retorna a ultima leitura de cada sensor de todos os equipamentos da planta")
def ultima_leitura():
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/leituras/ultima")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", streamable_http_path="/mcp", host="0.0.0.0")
