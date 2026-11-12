from mcp.server.mcpserver import MCPServer
import urllib.request as requisicao

NOME = "alarmes"
mcp = MCPServer(NOME)

URL_BASE = "http://alarmes:5000"

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

@mcp.tool(name="alarmes_por_equipamento", title="Alarmes por Equipamento", description="retorna os alarmes de um equipamento identificado pelo seu id. Equipamentos: 1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1")
def alarmes_por_equipamento(equipamento_id: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/alarmes/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="alarmes_por_severidade", title="Alarmes por Severidade", description="retorna alarmes filtrados por severidade (baixa, media, alta ou critica)")
def alarmes_por_severidade(severidade: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/alarmes/severidade/{severidade}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="resumo_alarmes", title="Resumo de Alarmes", description="retorna um resumo com a contagem de alarmes por equipamento e severidade")
def resumo_alarmes():
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/alarmes/resumo")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", streamable_http_path="/mcp", host="0.0.0.0")
