"""Gráficos das leituras de sensores para a interface web (app.py).

Cada grandeza tem unidade própria, então cada uma ganha o seu painel (sem dois
eixos no mesmo gráfico). Em cada painel, a barra cinza é a faixa de operação
(do setpoint mínimo ao máximo) e o ponto é o valor lido: verde dentro da faixa,
vermelho fora dela, com uma seta e um rótulo para não depender só da cor.
"""
import json

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ferramentas cujo resultado traz leituras de sensores
FERRAMENTAS_COM_LEITURAS = {
    "leituras_por_equipamento",
    "leituras_por_grandeza",
    "ultima_leitura",
    "diagnosticar_equipamento",
}

NOMES_GRANDEZAS = {"temperatura": "Temperatura", "pressao": "Pressão", "vibracao": "Vibração"}

COR_FAIXA = "rgba(138, 137, 132, 0.28)"
COR_DENTRO = "#0ca30c"   # status: normal
COR_FORA = "#d03b3b"     # status: crítico
COR_TEXTO = "#8a8984"    # legível nos temas claro e escuro do Chainlit
COR_GRADE = "rgba(138, 137, 132, 0.25)"


def desembrulhar_resultado(conteudo):
    """As ferramentas devolvem um texto JSON, que o servidor MCP embrulha em {"result": "<texto>"}."""
    if isinstance(conteudo, dict) and set(conteudo) == {"result"} and isinstance(conteudo["result"], str):
        try:
            return json.loads(conteudo["result"])
        except json.JSONDecodeError:
            return conteudo
    return conteudo


def extrair_leituras(nome_ferramenta, resultado):
    """Devolve a lista de leituras contida no resultado da ferramenta, ou [] se não houver."""
    if nome_ferramenta not in FERRAMENTAS_COM_LEITURAS:
        return []
    try:
        conteudo = desembrulhar_resultado(json.loads(resultado))
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(conteudo, dict):
        return []

    leituras = conteudo.get("leituras_atuais", conteudo.get("dados", []))
    if not isinstance(leituras, list):
        return []
    return [
        l for l in leituras
        if isinstance(l, dict) and isinstance(l.get("valor"), (int, float)) and l.get("grandeza")
    ]


def situacao(leitura):
    valor, minimo, maximo = leitura["valor"], leitura.get("setpoint_min"), leitura.get("setpoint_max")
    if maximo is not None and valor > maximo:
        return "▲ acima"
    if minimo is not None and valor < minimo:
        return "▼ abaixo"
    return "dentro da faixa"


def rotulo_eixo(leitura, varios_equipamentos):
    """Leituras de vários equipamentos são comparadas lado a lado; as de um só, ao longo do tempo."""
    if varios_equipamentos:
        return leitura.get("equipamento_nome") or f"Equipamento {leitura.get('equipamento_id')}"
    registrado = str(leitura.get("registrado_em", ""))
    return registrado.replace("T", " ")[:16] or f"Leitura {leitura.get('leitura_id')}"


def gerar_grafico(leituras, titulo):
    """Monta a figura com um painel por grandeza; devolve None se não houver o que desenhar."""
    if not leituras:
        return None

    grandezas = [g for g in NOMES_GRANDEZAS if any(l["grandeza"] == g for l in leituras)]
    grandezas += sorted({l["grandeza"] for l in leituras} - set(grandezas))
    varios_equipamentos = len({l.get("equipamento_id") for l in leituras}) > 1

    titulos = []
    for g in grandezas:
        unidade = next((l.get("unidade") for l in leituras if l["grandeza"] == g and l.get("unidade")), "")
        titulos.append(f"{NOMES_GRANDEZAS.get(g, g.capitalize())} ({unidade})" if unidade else NOMES_GRANDEZAS.get(g, g))

    figura = make_subplots(rows = len(grandezas), cols = 1, subplot_titles = titulos, vertical_spacing = 0.14)

    for linha, g in enumerate(grandezas, start = 1):
        do_painel = sorted(
            (l for l in leituras if l["grandeza"] == g),
            key = lambda l: (str(l.get("registrado_em", "")), l.get("equipamento_id") or 0)
        )
        eixo = [rotulo_eixo(l, varios_equipamentos) for l in do_painel]
        unidade = do_painel[0].get("unidade") or ""

        com_faixa = [l for l in do_painel if l.get("setpoint_min") is not None and l.get("setpoint_max") is not None]
        if com_faixa:
            figura.add_trace(go.Bar(
                x = [rotulo_eixo(l, varios_equipamentos) for l in com_faixa],
                y = [l["setpoint_max"] - l["setpoint_min"] for l in com_faixa],
                base = [l["setpoint_min"] for l in com_faixa],
                marker = dict(color = COR_FAIXA, line = dict(width = 0), cornerradius = 4),
                width = 0.5,
                name = "Faixa de operação (setpoints)",
                legendgroup = "faixa",
                showlegend = linha == 1,
                customdata = [[l["setpoint_min"], l["setpoint_max"]] for l in com_faixa],
                hovertemplate = f"Faixa de operação: %{{customdata[0]}} a %{{customdata[1]}} {unidade}<extra></extra>",
            ), row = linha, col = 1)

        situacoes = [situacao(l) for l in do_painel]
        figura.add_trace(go.Scatter(
            x = eixo,
            y = [l["valor"] for l in do_painel],
            mode = "markers+text",
            marker = dict(
                size = 12,
                color = [COR_DENTRO if s == "dentro da faixa" else COR_FORA for s in situacoes],
                line = dict(width = 2, color = "rgba(255, 255, 255, 0.9)"),
            ),
            # rótulo direto só onde importa: nas leituras fora da faixa
            text = [s if s != "dentro da faixa" else "" for s in situacoes],
            textposition = "top center",
            cliponaxis = False,
            textfont = dict(color = COR_TEXTO, size = 11),
            name = "Valor lido",
            legendgroup = "valor",
            showlegend = linha == 1,
            customdata = [[l.get("equipamento_nome", ""), s] for l, s in zip(do_painel, situacoes)],
            hovertemplate = f"%{{customdata[0]}}<br>Valor lido: %{{y}} {unidade}<br>%{{customdata[1]}}<extra></extra>",
        ), row = linha, col = 1)

        # folga acima do maior valor, para o rótulo do ponto não encostar no título do painel
        limites = [l["valor"] for l in do_painel] + [l[c] for l in com_faixa for c in ("setpoint_min", "setpoint_max")]
        menor, maior = min(limites), max(limites)
        folga = (maior - menor) * 0.2 or abs(maior) * 0.2 or 1
        figura.update_yaxes(range = [menor - folga * 0.4, maior + folga], row = linha, col = 1)

    altura = 230 * len(grandezas) + 150
    margem_superior, margem_inferior = 80, 80
    figura.update_layout(
        title = dict(text = titulo, font = dict(size = 15), x = 0, xref = "paper", xanchor = "left", y = 1 - 24 / altura, yanchor = "top"),
        height = altura,
        margin = dict(l = 50, r = 30, t = margem_superior, b = margem_inferior),
        paper_bgcolor = "rgba(0, 0, 0, 0)",
        plot_bgcolor = "rgba(0, 0, 0, 0)",
        font = dict(color = COR_TEXTO, size = 12),
        # legenda abaixo do último painel, longe do título e dos títulos dos painéis
        legend = dict(orientation = "h", yanchor = "top", y = -40 / (altura - margem_superior - margem_inferior), xanchor = "left", x = 0),
        barmode = "overlay",
        hoverlabel = dict(font_size = 12),
    )
    figura.update_xaxes(showgrid = False, linecolor = COR_GRADE, type = "category")
    figura.update_yaxes(gridcolor = COR_GRADE, zeroline = False)
    figura.update_annotations(font = dict(size = 13, color = COR_TEXTO))

    return figura
