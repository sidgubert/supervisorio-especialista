from flask import Flask, jsonify, make_response
import psycopg as dados
from psycopg.rows import dict_row as dicionario
from flask_cors import CORS

servico = Flask("sensores")
CORS(servico)

DESCRICAO = "serviço de leituras de sensores da planta industrial PlantaView"
VERSAO = "1.0"

SERVIDOR_BANCO = "dados-sensores"
PORTA_BANCO = 5432
USUARIO_BANCO = "admin"
SENHA_BANCO = "admin"
NOME_BANCO = "plantaview_sensores"

def get_conexao_com_bd():
    conexao = dados.connect(
        host = SERVIDOR_BANCO,
        port = PORTA_BANCO,
        user = USUARIO_BANCO,
        password = SENHA_BANCO,
        dbname = NOME_BANCO,
        row_factory = dicionario,
        options = "-c search_path=plantaview"
    )
    return conexao

@servico.get("/")
def get_info():
    return make_response(jsonify(descricao = DESCRICAO, versao = VERSAO), 200)

@servico.get("/leituras")
def get_todas_leituras():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_leituras_detalhadas ORDER BY registrado_em DESC LIMIT 100")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/leituras/equipamento/<int:id_equipamento>")
def get_leituras_equipamento(id_equipamento):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_leituras_detalhadas WHERE equipamento_id = %s ORDER BY registrado_em DESC", (id_equipamento,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/leituras/equipamento/<int:id_equipamento>/grandeza/<string:grandeza>")
def get_leituras_equipamento_grandeza(id_equipamento, grandeza):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_leituras_detalhadas WHERE equipamento_id = %s AND grandeza = %s ORDER BY registrado_em DESC", (id_equipamento, grandeza))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/leituras/periodo/<string:inicio>/<string:fim>")
def get_leituras_periodo(inicio, fim):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_leituras_detalhadas WHERE registrado_em BETWEEN %s AND %s ORDER BY registrado_em DESC", (inicio, fim))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/leituras/ultima")
def get_ultima_leitura():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_ultima_leitura")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

if __name__ == "__main__":
    servico.run(host="0.0.0.0", debug=True)
