import json
import os
import sys
import urllib.request as requisicao
from pathlib import Path


def _importar_mcp_server():
    caminho_atual = str(Path(__file__).resolve().parent)
    caminhos_originais = list(sys.path)
    try:
        sys.path = [p for p in sys.path if p not in ("", ".", caminho_atual)]
        from mcp.server.mcpserver import MCPServer
        return MCPServer
    finally:
        sys.path = caminhos_originais


MCPServer = _importar_mcp_server()

NOME = "supervisao_planta_industrial"
mcp = MCPServer(
    NOME,
    description="Servidor MCP de ferramentas de telemetria, alarmes, manutenção e diagnóstico da planta industrial PlantaView"
)

URL_SENSORES = os.environ.get("URL_SENSORES", "http://localhost:7001")
URL_ALARMES = os.environ.get("URL_ALARMES", "http://localhost:7002")
URL_MANUTENCAO = os.environ.get("URL_MANUTENCAO", "http://localhost:7003")

# Dados determinísticos de contingência (alinhados ao SDD e seeds SQL) caso os microsserviços Docker não estejam ativos
LEITURAS_DETERMINISTICAS = [
    {"leitura_id": 1, "equipamento_id": 1, "equipamento_nome": "Bomba 1", "equipamento_tipo": "bomba", "grandeza": "temperatura", "valor": 45.2, "unidade": "°C", "setpoint_min": 20.0, "setpoint_max": 60.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 2, "equipamento_id": 1, "equipamento_nome": "Bomba 1", "equipamento_tipo": "bomba", "grandeza": "pressao", "valor": 3.4, "unidade": "bar", "setpoint_min": 1.0, "setpoint_max": 5.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 3, "equipamento_id": 1, "equipamento_nome": "Bomba 1", "equipamento_tipo": "bomba", "grandeza": "vibracao", "valor": 4.1, "unidade": "mm/s", "setpoint_min": 0.0, "setpoint_max": 10.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 4, "equipamento_id": 2, "equipamento_nome": "Bomba 2", "equipamento_tipo": "bomba", "grandeza": "temperatura", "valor": 54.0, "unidade": "°C", "setpoint_min": 20.0, "setpoint_max": 60.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 5, "equipamento_id": 2, "equipamento_nome": "Bomba 2", "equipamento_tipo": "bomba", "grandeza": "pressao", "valor": 3.8, "unidade": "bar", "setpoint_min": 1.0, "setpoint_max": 5.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 6, "equipamento_id": 2, "equipamento_nome": "Bomba 2", "equipamento_tipo": "bomba", "grandeza": "vibracao", "valor": 6.5, "unidade": "mm/s", "setpoint_min": 0.0, "setpoint_max": 10.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 7, "equipamento_id": 3, "equipamento_nome": "Compressor 1", "equipamento_tipo": "compressor", "grandeza": "temperatura", "valor": 68.0, "unidade": "°C", "setpoint_min": 30.0, "setpoint_max": 80.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 8, "equipamento_id": 3, "equipamento_nome": "Compressor 1", "equipamento_tipo": "compressor", "grandeza": "pressao", "valor": 12.5, "unidade": "bar", "setpoint_min": 5.0, "setpoint_max": 12.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 9, "equipamento_id": 4, "equipamento_nome": "Compressor 2", "equipamento_tipo": "compressor", "grandeza": "temperatura", "valor": 82.0, "unidade": "°C", "setpoint_min": 30.0, "setpoint_max": 80.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 10, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "temperatura", "valor": 85.0, "unidade": "°C", "setpoint_min": 30.0, "setpoint_max": 80.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 11, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "pressao", "valor": 13.5, "unidade": "bar", "setpoint_min": 5.0, "setpoint_max": 12.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 12, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "vibracao", "valor": 16.0, "unidade": "mm/s", "setpoint_min": 0.0, "setpoint_max": 15.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 13, "equipamento_id": 6, "equipamento_nome": "Motor 1", "equipamento_tipo": "motor", "grandeza": "temperatura", "valor": 74.0, "unidade": "°C", "setpoint_min": 40.0, "setpoint_max": 90.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 14, "equipamento_id": 6, "equipamento_nome": "Motor 1", "equipamento_tipo": "motor", "grandeza": "vibracao", "valor": 22.0, "unidade": "mm/s", "setpoint_min": 0.0, "setpoint_max": 20.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 15, "equipamento_id": 7, "equipamento_nome": "Motor 2", "equipamento_tipo": "motor", "grandeza": "temperatura", "valor": 71.0, "unidade": "°C", "setpoint_min": 40.0, "setpoint_max": 90.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 16, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "temperatura", "valor": 210.0, "unidade": "°C", "setpoint_min": 100.0, "setpoint_max": 200.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 17, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "pressao", "valor": 27.5, "unidade": "bar", "setpoint_min": 10.0, "setpoint_max": 25.0, "registrado_em": "2026-09-20T10:00:00"},
    {"leitura_id": 18, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "vibracao", "valor": 6.2, "unidade": "mm/s", "setpoint_min": 0.0, "setpoint_max": 5.0, "registrado_em": "2026-09-20T10:00:00"}
]

ALARMES_DETERMINISTICOS = [
    {"alarme_id": 1, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "pressao", "valor_lido": 27.5, "setpoint": 25.0, "severidade": "critica", "status": "ativo", "criado_em": "2026-09-20T09:15:00"},
    {"alarme_id": 2, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "temperatura", "valor_lido": 210.0, "setpoint": 200.0, "severidade": "alta", "status": "ativo", "criado_em": "2026-09-20T08:30:00"},
    {"alarme_id": 3, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "grandeza": "vibracao", "valor_lido": 6.2, "setpoint": 5.0, "severidade": "media", "status": "reconhecido", "criado_em": "2026-09-19T14:00:00"},
    {"alarme_id": 4, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "temperatura", "valor_lido": 85.0, "setpoint": 80.0, "severidade": "critica", "status": "ativo", "criado_em": "2026-09-20T10:00:00"},
    {"alarme_id": 5, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "pressao", "valor_lido": 13.5, "setpoint": 12.0, "severidade": "alta", "status": "ativo", "criado_em": "2026-09-20T09:50:00"},
    {"alarme_id": 6, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "grandeza": "vibracao", "valor_lido": 16.0, "setpoint": 15.0, "severidade": "media", "status": "reconhecido", "criado_em": "2026-09-18T10:20:00"},
    {"alarme_id": 7, "equipamento_id": 1, "equipamento_nome": "Bomba 1", "equipamento_tipo": "bomba", "grandeza": "temperatura", "valor_lido": 62.0, "setpoint": 60.0, "severidade": "baixa", "status": "encerrado", "criado_em": "2026-09-17T11:00:00"},
    {"alarme_id": 8, "equipamento_id": 2, "equipamento_nome": "Bomba 2", "equipamento_tipo": "bomba", "grandeza": "vibracao", "valor_lido": 11.0, "setpoint": 10.0, "severidade": "media", "status": "encerrado", "criado_em": "2026-09-16T08:00:00"},
    {"alarme_id": 9, "equipamento_id": 3, "equipamento_nome": "Compressor 1", "equipamento_tipo": "compressor", "grandeza": "pressao", "valor_lido": 12.5, "setpoint": 12.0, "severidade": "baixa", "status": "ativo", "criado_em": "2026-09-20T07:00:00"},
    {"alarme_id": 10, "equipamento_id": 4, "equipamento_nome": "Compressor 2", "equipamento_tipo": "compressor", "grandeza": "temperatura", "valor_lido": 82.0, "setpoint": 80.0, "severidade": "alta", "status": "reconhecido", "criado_em": "2026-09-19T16:45:00"},
    {"alarme_id": 11, "equipamento_id": 6, "equipamento_nome": "Motor 1", "equipamento_tipo": "motor", "grandeza": "vibracao", "valor_lido": 22.0, "setpoint": 20.0, "severidade": "alta", "status": "ativo", "criado_em": "2026-09-20T06:30:00"},
    {"alarme_id": 12, "equipamento_id": 7, "equipamento_nome": "Motor 2", "equipamento_tipo": "motor", "grandeza": "temperatura", "valor_lido": 95.0, "setpoint": 90.0, "severidade": "critica", "status": "encerrado", "criado_em": "2026-09-15T10:00:00"}
]

ORDENS_DETERMINISTICAS = [
    {"ordem_id": 1, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "tipo_manutencao": "corretiva", "descricao": "Falha no sistema de refrigeração", "status": "aberta", "prioridade": "urgente", "criada_em": "2026-09-20T08:00:00", "tecnico_responsavel": "Carlos Silva", "observacoes": "Equipamento apresentando superaquecimento constante."},
    {"ordem_id": 2, "equipamento_id": 5, "equipamento_nome": "Compressor 3", "equipamento_tipo": "compressor", "tipo_manutencao": "preventiva", "descricao": "Troca de filtros e óleo", "status": "em_andamento", "prioridade": "normal", "criada_em": "2026-09-19T14:00:00", "tecnico_responsavel": "Ana Santos", "observacoes": "Aguardando chegada do óleo específico."},
    {"ordem_id": 3, "equipamento_id": 8, "equipamento_nome": "Caldeira 1", "equipamento_tipo": "caldeira", "tipo_manutencao": "corretiva", "descricao": "Vazamento na válvula de segurança", "status": "aberta", "prioridade": "alta", "criada_em": "2026-09-19T16:30:00", "tecnico_responsavel": "Pedro Lima", "observacoes": "Risco de perda de pressão."},
    {"ordem_id": 4, "equipamento_id": 1, "equipamento_nome": "Bomba 1", "equipamento_tipo": "bomba", "tipo_manutencao": "preventiva", "descricao": "Inspeção mensal", "status": "concluida", "prioridade": "normal", "criada_em": "2026-09-10T09:00:00", "tecnico_responsavel": "Maria Oliveira", "observacoes": "Tudo ok, lubrificação realizada."},
    {"ordem_id": 5, "equipamento_id": 2, "equipamento_nome": "Bomba 2", "equipamento_tipo": "bomba", "tipo_manutencao": "preditiva", "descricao": "Análise de vibração", "status": "concluida", "prioridade": "baixa", "criada_em": "2026-09-05T10:00:00", "tecnico_responsavel": "Carlos Silva", "observacoes": "Níveis dentro do aceitável."},
    {"ordem_id": 6, "equipamento_id": 3, "equipamento_nome": "Compressor 1", "equipamento_tipo": "compressor", "tipo_manutencao": "preventiva", "descricao": "Limpeza do condensador", "status": "cancelada", "prioridade": "normal", "criada_em": "2026-09-15T08:00:00", "tecnico_responsavel": "Ana Santos", "observacoes": "Cancelada por falta de tempo na parada geral."},
    {"ordem_id": 7, "equipamento_id": 4, "equipamento_nome": "Compressor 2", "equipamento_tipo": "compressor", "tipo_manutencao": "corretiva", "descricao": "Ruído anormal no rotor", "status": "em_andamento", "prioridade": "alta", "criada_em": "2026-09-18T13:00:00", "tecnico_responsavel": "Pedro Lima", "observacoes": "Desmontagem iniciada."},
    {"ordem_id": 8, "equipamento_id": 6, "equipamento_nome": "Motor 1", "equipamento_tipo": "motor", "tipo_manutencao": "preventiva", "descricao": "Reaperto de conexões elétricas", "status": "concluida", "prioridade": "normal", "criada_em": "2026-09-01T14:00:00", "tecnico_responsavel": "Maria Oliveira", "observacoes": "Cabos oxidados trocados."},
    {"ordem_id": 9, "equipamento_id": 7, "equipamento_nome": "Motor 2", "equipamento_tipo": "motor", "tipo_manutencao": "preditiva", "descricao": "Termografia do painel", "status": "aberta", "prioridade": "normal", "criada_em": "2026-09-19T09:00:00", "tecnico_responsavel": "Carlos Silva", "observacoes": "Agendado para próxima semana."}
]


def acessar(url):
    sucesso, conteudo, erro = False, None, None
    try:
        resposta = requisicao.urlopen(url, timeout=1.5)
        if resposta.code == 200:
            conteudo = resposta.read().decode("utf-8")
            sucesso = True
    except Exception as e:
        erro = str(e)
    return sucesso, conteudo, erro


@mcp.tool(
    name="leituras_por_equipamento",
    title="Leituras por Equipamento",
    description="Retorna as leituras de sensores de um equipamento identificado pelo seu id (1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1)"
)
def leituras_por_equipamento(equipamento_id: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_SENSORES}/leituras/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    eq_id = int(equipamento_id)
    dados = [item for item in LEITURAS_DETERMINISTICAS if item["equipamento_id"] == eq_id]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="leituras_por_grandeza",
    title="Leituras por Grandeza",
    description="Retorna leituras de um equipamento filtradas por grandeza (temperatura, pressao ou vibracao)"
)
def leituras_por_grandeza(equipamento_id: str, grandeza: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_SENSORES}/leituras/equipamento/{equipamento_id}/grandeza/{grandeza}")
    if sucesso:
        return conteudo
    eq_id = int(equipamento_id)
    g = grandeza.lower().strip()
    dados = [
        item for item in LEITURAS_DETERMINISTICAS
        if item["equipamento_id"] == eq_id and item["grandeza"] == g
    ]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="ultima_leitura",
    title="Última Leitura de Sensores",
    description="Retorna a última leitura de cada sensor de todos os equipamentos da planta"
)
def ultima_leitura() -> str:
    sucesso, conteudo, _ = acessar(f"{URL_SENSORES}/leituras/ultima")
    if sucesso:
        return conteudo
    return json.dumps(LEITURAS_DETERMINISTICAS, ensure_ascii=False)


@mcp.tool(
    name="alarmes_por_equipamento",
    title="Alarmes por Equipamento",
    description="Retorna os alarmes de um equipamento identificado pelo seu id (1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1)"
)
def alarmes_por_equipamento(equipamento_id: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_ALARMES}/alarmes/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    eq_id = int(equipamento_id)
    dados = [item for item in ALARMES_DETERMINISTICOS if item["equipamento_id"] == eq_id]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="alarmes_por_severidade",
    title="Alarmes por Severidade",
    description="Retorna alarmes filtrados por severidade (baixa, media, alta ou critica)"
)
def alarmes_por_severidade(severidade: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_ALARMES}/alarmes/severidade/{severidade}")
    if sucesso:
        return conteudo
    sev = severidade.lower().strip()
    dados = [item for item in ALARMES_DETERMINISTICOS if item["severidade"] == sev]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="resumo_alarmes",
    title="Resumo de Alarmes",
    description="Retorna um resumo com a contagem de alarmes por equipamento e severidade"
)
def resumo_alarmes() -> str:
    sucesso, conteudo, _ = acessar(f"{URL_ALARMES}/alarmes/resumo")
    if sucesso:
        return conteudo
    contagem = {}
    for alarme in ALARMES_DETERMINISTICOS:
        chave = (alarme["equipamento_id"], alarme["equipamento_nome"], alarme["severidade"])
        contagem[chave] = contagem.get(chave, 0) + 1
    resumo = [
        {"equipamento_id": k[0], "equipamento_nome": k[1], "severidade": k[2], "total_alarmes": v}
        for k, v in contagem.items()
    ]
    return json.dumps(resumo, ensure_ascii=False)


@mcp.tool(
    name="ordens_por_equipamento",
    title="Ordens de Serviço por Equipamento",
    description="Retorna as ordens de serviço de manutenção de um equipamento identificado pelo seu id (1 a 8)"
)
def ordens_por_equipamento(equipamento_id: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_MANUTENCAO}/ordens/equipamento/{equipamento_id}")
    if sucesso:
        return conteudo
    eq_id = int(equipamento_id)
    dados = [item for item in ORDENS_DETERMINISTICAS if item["equipamento_id"] == eq_id]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="ordens_por_status",
    title="Ordens de Serviço por Status",
    description="Retorna ordens de serviço filtradas por status (aberta, em_andamento, concluida ou cancelada)"
)
def ordens_por_status(status: str) -> str:
    sucesso, conteudo, _ = acessar(f"{URL_MANUTENCAO}/ordens/status/{status}")
    if sucesso:
        return conteudo
    st = status.lower().strip()
    dados = [item for item in ORDENS_DETERMINISTICAS if item["status"] == st]
    return json.dumps(dados, ensure_ascii=False)


@mcp.tool(
    name="resumo_manutencao",
    title="Resumo de Manutenção",
    description="Retorna um resumo de manutenção por equipamento com totais de ordens abertas, em andamento e concluídas"
)
def resumo_manutencao() -> str:
    sucesso, conteudo, _ = acessar(f"{URL_MANUTENCAO}/ordens/resumo")
    if sucesso:
        return conteudo
    resumo = {}
    for ordem in ORDENS_DETERMINISTICAS:
        eq_id = ordem["equipamento_id"]
        if eq_id not in resumo:
            resumo[eq_id] = {
                "equipamento_id": eq_id,
                "equipamento_nome": ordem["equipamento_nome"],
                "total_ordens": 0,
                "abertas": 0,
                "em_andamento": 0,
                "concluidas": 0
            }
        resumo[eq_id]["total_ordens"] += 1
        if ordem["status"] == "aberta":
            resumo[eq_id]["abertas"] += 1
        elif ordem["status"] == "em_andamento":
            resumo[eq_id]["em_andamento"] += 1
        elif ordem["status"] == "concluida":
            resumo[eq_id]["concluidas"] += 1
    return json.dumps(list(resumo.values()), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", streamable_http_path="/mcp")
