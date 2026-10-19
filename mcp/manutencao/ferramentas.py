from mcp.server.mcpserver import MCPServer
import urllib.request as requisicao

NOME = "manutencao"
mcp = MCPServer(NOME)

URL_BASE = "http://manutencao:5000"

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

@mcp.tool(name="ordens_por_equipamento", title="Ordens por Equipamento", description="retorna as ordens de servico de manutencao de um equipamento identificado pelo seu id. Equipamentos: 1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1")
def ordens_por_equipamento(equipamento_id: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/ordens/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="ordens_por_status", title="Ordens por Status", description="retorna ordens de servico filtradas por status (aberta, em_andamento, concluida ou cancelada)")
def ordens_por_status(status: str):
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/ordens/status/{status}")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

@mcp.tool(name="resumo_manutencao", title="Resumo de Manutencao", description="retorna um resumo de manutencao por equipamento com totais de ordens abertas, em andamento e concluidas")
def resumo_manutencao():
    sucesso, conteudo, erro = acessar(f"{URL_BASE}/ordens/resumo")
    if sucesso:
        return conteudo
    else:
        return f"ocorreu um erro: {erro}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", streamable_http_path="/mcp", host="0.0.0.0")
