import json
import os
import unicodedata
import urllib.request as requisicao

from mcp.server.mcpserver import MCPServer

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


EQUIPAMENTOS = {
    1: "Bomba 1", 2: "Bomba 2", 3: "Compressor 1", 4: "Compressor 2",
    5: "Compressor 3", 6: "Motor 1", 7: "Motor 2", 8: "Caldeira 1"
}
GRANDEZAS = ("temperatura", "pressao", "vibracao")
SEVERIDADES = ("baixa", "media", "alta", "critica")
STATUS_ORDENS = ("aberta", "em_andamento", "concluida", "cancelada")

FONTE_SERVICOS = "microsserviços da planta (tempo real)"
FONTE_CONTINGENCIA = "contingência: microsserviços indisponíveis, dados simulados de 2026-09-20"


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


def consultar(url, contingencia):
    """Consulta o microsserviço; se ele não responder, usa os dados de contingência.

    Retorna (dados, fonte), para que a origem do dado nunca fique oculta.
    """
    sucesso, conteudo, _ = acessar(url)
    if sucesso:
        try:
            return json.loads(conteudo), FONTE_SERVICOS
        except json.JSONDecodeError:
            pass
    return contingencia(), FONTE_CONTINGENCIA


def normalizar(texto):
    sem_acentos = unicodedata.normalize("NFKD", str(texto))
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return " ".join(sem_acentos.lower().split())


def resolver_equipamento(valor):
    """Aceita o id (8, "8", "8.0") ou o nome ("Caldeira 1") e devolve o id, ou None."""
    texto = normalizar(valor)
    try:
        eq_id = int(float(texto))
        return eq_id if eq_id in EQUIPAMENTOS else None
    except ValueError:
        pass
    for eq_id, nome in EQUIPAMENTOS.items():
        if normalizar(nome) in texto:
            return eq_id
    return None


def resolver_opcao(valor, opcoes):
    texto = normalizar(valor).replace(" ", "_")
    return texto if texto in opcoes else None


def responder(dados, fonte):
    return json.dumps({"fonte": fonte, "dados": dados}, ensure_ascii=False)


def responder_erro(mensagem):
    return json.dumps({"erro": mensagem}, ensure_ascii=False)


ERRO_EQUIPAMENTO = "equipamento desconhecido; informe o id de 1 a 8: " + ", ".join(
    f"{eq_id}={nome}" for eq_id, nome in EQUIPAMENTOS.items()
)


def obter_leituras(eq_id):
    return consultar(
        f"{URL_SENSORES}/leituras/equipamento/{eq_id}",
        lambda: [item for item in LEITURAS_DETERMINISTICAS if item["equipamento_id"] == eq_id]
    )


def obter_alarmes(eq_id):
    return consultar(
        f"{URL_ALARMES}/alarmes/equipamento/{eq_id}",
        lambda: [item for item in ALARMES_DETERMINISTICOS if item["equipamento_id"] == eq_id]
    )


def obter_ordens(eq_id):
    return consultar(
        f"{URL_MANUTENCAO}/ordens/equipamento/{eq_id}",
        lambda: [item for item in ORDENS_DETERMINISTICAS if item["equipamento_id"] == eq_id]
    )


def detectar_desvios(leituras):
    """Compara a leitura mais recente de cada grandeza com os setpoints mínimo e máximo."""
    desvios, grandezas_vistas = [], set()

    for leitura in sorted(leituras, key=lambda l: str(l.get("registrado_em", "")), reverse=True):
        grandeza = leitura.get("grandeza")
        if grandeza in grandezas_vistas:
            continue
        grandezas_vistas.add(grandeza)

        try:
            valor = float(leitura["valor"])
        except (KeyError, TypeError, ValueError):
            continue

        for limite, tipo in (("setpoint_max", "acima do máximo"), ("setpoint_min", "abaixo do mínimo")):
            if leitura.get(limite) is None:
                continue
            setpoint = float(leitura[limite])
            if (limite == "setpoint_max" and valor > setpoint) or (limite == "setpoint_min" and valor < setpoint):
                desvios.append({
                    "grandeza": grandeza,
                    "valor_lido": valor,
                    "desvio": tipo,
                    "setpoint": setpoint,
                    "unidade": leitura.get("unidade")
                })

    return desvios


@mcp.tool(
    name="leituras_por_equipamento",
    title="Leituras por Equipamento",
    description="Retorna as leituras de sensores de um equipamento identificado pelo seu id (1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1)"
)
def leituras_por_equipamento(equipamento_id: str | int) -> str:
    eq_id = resolver_equipamento(equipamento_id)
    if eq_id is None:
        return responder_erro(ERRO_EQUIPAMENTO)
    return responder(*obter_leituras(eq_id))


@mcp.tool(
    name="leituras_por_grandeza",
    title="Leituras por Grandeza",
    description="Retorna leituras de um equipamento (id 1 a 8) filtradas por grandeza (temperatura, pressao ou vibracao)"
)
def leituras_por_grandeza(equipamento_id: str | int, grandeza: str) -> str:
    eq_id = resolver_equipamento(equipamento_id)
    if eq_id is None:
        return responder_erro(ERRO_EQUIPAMENTO)
    g = resolver_opcao(grandeza, GRANDEZAS)
    if g is None:
        return responder_erro(f"grandeza desconhecida; use uma destas: {', '.join(GRANDEZAS)}")
    return responder(*consultar(
        f"{URL_SENSORES}/leituras/equipamento/{eq_id}/grandeza/{g}",
        lambda: [
            item for item in LEITURAS_DETERMINISTICAS
            if item["equipamento_id"] == eq_id and item["grandeza"] == g
        ]
    ))


@mcp.tool(
    name="ultima_leitura",
    title="Última Leitura de Sensores",
    description="Retorna a última leitura de cada sensor de todos os equipamentos da planta"
)
def ultima_leitura() -> str:
    return responder(*consultar(f"{URL_SENSORES}/leituras/ultima", lambda: LEITURAS_DETERMINISTICAS))


@mcp.tool(
    name="alarmes_por_equipamento",
    title="Alarmes por Equipamento",
    description="Retorna os alarmes de um equipamento identificado pelo seu id (1=Bomba 1, 2=Bomba 2, 3=Compressor 1, 4=Compressor 2, 5=Compressor 3, 6=Motor 1, 7=Motor 2, 8=Caldeira 1)"
)
def alarmes_por_equipamento(equipamento_id: str | int) -> str:
    eq_id = resolver_equipamento(equipamento_id)
    if eq_id is None:
        return responder_erro(ERRO_EQUIPAMENTO)
    return responder(*obter_alarmes(eq_id))


@mcp.tool(
    name="alarmes_por_severidade",
    title="Alarmes por Severidade",
    description="Retorna alarmes filtrados por severidade (baixa, media, alta ou critica)"
)
def alarmes_por_severidade(severidade: str) -> str:
    sev = resolver_opcao(severidade, SEVERIDADES)
    if sev is None:
        return responder_erro(f"severidade desconhecida; use uma destas: {', '.join(SEVERIDADES)}")
    return responder(*consultar(
        f"{URL_ALARMES}/alarmes/severidade/{sev}",
        lambda: [item for item in ALARMES_DETERMINISTICOS if item["severidade"] == sev]
    ))


def resumir_alarmes_contingencia():
    contagem = {}
    for alarme in ALARMES_DETERMINISTICOS:
        chave = (alarme["equipamento_id"], alarme["equipamento_nome"], alarme["severidade"])
        contagem[chave] = contagem.get(chave, 0) + 1
    return [
        {"equipamento_id": k[0], "equipamento_nome": k[1], "severidade": k[2], "total_alarmes": v}
        for k, v in contagem.items()
    ]


@mcp.tool(
    name="resumo_alarmes",
    title="Resumo de Alarmes",
    description="Retorna um resumo com a contagem de alarmes por equipamento e severidade"
)
def resumo_alarmes() -> str:
    return responder(*consultar(f"{URL_ALARMES}/alarmes/resumo", resumir_alarmes_contingencia))


@mcp.tool(
    name="ordens_por_equipamento",
    title="Ordens de Serviço por Equipamento",
    description="Retorna as ordens de serviço de manutenção de um equipamento identificado pelo seu id (1 a 8)"
)
def ordens_por_equipamento(equipamento_id: str | int) -> str:
    eq_id = resolver_equipamento(equipamento_id)
    if eq_id is None:
        return responder_erro(ERRO_EQUIPAMENTO)
    return responder(*obter_ordens(eq_id))


@mcp.tool(
    name="ordens_por_status",
    title="Ordens de Serviço por Status",
    description="Retorna ordens de serviço filtradas por status (aberta, em_andamento, concluida ou cancelada)"
)
def ordens_por_status(status: str) -> str:
    st = resolver_opcao(status, STATUS_ORDENS)
    if st is None:
        return responder_erro(f"status desconhecido; use um destes: {', '.join(STATUS_ORDENS)}")
    return responder(*consultar(
        f"{URL_MANUTENCAO}/ordens/status/{st}",
        lambda: [item for item in ORDENS_DETERMINISTICAS if item["status"] == st]
    ))


def resumir_manutencao_contingencia():
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
    return list(resumo.values())


@mcp.tool(
    name="resumo_manutencao",
    title="Resumo de Manutenção",
    description="Retorna um resumo de manutenção por equipamento com totais de ordens abertas, em andamento e concluídas"
)
def resumo_manutencao() -> str:
    return responder(*consultar(f"{URL_MANUTENCAO}/ordens/resumo", resumir_manutencao_contingencia))


@mcp.tool(
    name="diagnosticar_equipamento",
    title="Diagnóstico Integrado de Equipamento",
    description="Consolida leituras atuais de sensores, desvios de setpoint, alarmes ativos e ordens de serviço pendentes para o diagnóstico de um equipamento (id 1 a 8)"
)
def diagnosticar_equipamento(equipamento_id: str | int) -> str:
    eq_id = resolver_equipamento(equipamento_id)
    if eq_id is None:
        return responder_erro(ERRO_EQUIPAMENTO)

    leituras, fonte_leituras = obter_leituras(eq_id)
    alarmes, fonte_alarmes = obter_alarmes(eq_id)
    ordens, fonte_ordens = obter_ordens(eq_id)

    desvios = detectar_desvios(leituras)
    alarmes_ativos = [a for a in alarmes if a.get("status") == "ativo"]
    ordens_pendentes = [o for o in ordens if o.get("status") in ("aberta", "em_andamento")]

    fontes = {fonte_leituras, fonte_alarmes, fonte_ordens}
    diagnostico = {
        "fonte": FONTE_CONTINGENCIA if FONTE_CONTINGENCIA in fontes else FONTE_SERVICOS,
        "equipamento_id": eq_id,
        "equipamento_nome": EQUIPAMENTOS[eq_id],
        "status_operacional": "ANORMAL" if (desvios or alarmes_ativos) else "NORMAL",
        "desvios_setpoint_detectados": desvios,
        "alarmes_ativos": alarmes_ativos,
        "ordens_servico_pendentes": ordens_pendentes,
        "leituras_atuais": leituras
    }
    return json.dumps(diagnostico, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", streamable_http_path="/mcp")
