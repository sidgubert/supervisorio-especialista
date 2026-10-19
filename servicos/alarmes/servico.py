from flask import Flask, jsonify, make_response
import psycopg as dados
from psycopg.rows import dict_row as dicionario
from flask_cors import CORS

servico = Flask("alarmes")
CORS(servico)

DESCRICAO = "serviço de alarmes de limite excedido da planta industrial PlantaView"
VERSAO = "1.0"

SERVIDOR_BANCO = "dados-alarmes"
PORTA_BANCO = 5432
USUARIO_BANCO = "admin"
SENHA_BANCO = "admin"
NOME_BANCO = "plantaview_alarmes"

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

@servico.get("/alarmes")
def get_todos_alarmes():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_alarmes_detalhados ORDER BY criado_em DESC")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/alarmes/equipamento/<int:id_equipamento>")
def get_alarmes_equipamento(id_equipamento):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_alarmes_detalhados WHERE equipamento_id = %s ORDER BY criado_em DESC", (id_equipamento,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/alarmes/status/<string:status>")
def get_alarmes_status(status):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_alarmes_detalhados WHERE status = %s ORDER BY criado_em DESC", (status,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/alarmes/severidade/<string:severidade>")
def get_alarmes_severidade(severidade):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_alarmes_detalhados WHERE severidade = %s ORDER BY criado_em DESC", (severidade,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/alarmes/resumo")
def get_alarmes_resumo():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_alarmes_por_equipamento")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

if __name__ == "__main__":
    servico.run(host="0.0.0.0", debug=True)
