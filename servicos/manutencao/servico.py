from flask import Flask, jsonify, make_response
import psycopg as dados
from psycopg.rows import dict_row as dicionario
from flask_cors import CORS

servico = Flask("manutencao")
CORS(servico)

DESCRICAO = "serviço de manutenção e ordens de serviço da planta industrial PlantaView"
VERSAO = "1.0"

SERVIDOR_BANCO = "dados-manutencao"
PORTA_BANCO = 5432
USUARIO_BANCO = "admin"
SENHA_BANCO = "admin"
NOME_BANCO = "plantaview_manutencao"

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

@servico.get("/ordens")
def get_todas_ordens():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_ordens_detalhadas ORDER BY criada_em DESC")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/ordens/equipamento/<int:id_equipamento>")
def get_ordens_equipamento(id_equipamento):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_ordens_detalhadas WHERE equipamento_id = %s ORDER BY criada_em DESC", (id_equipamento,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/ordens/status/<string:status>")
def get_ordens_status(status):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_ordens_detalhadas WHERE status = %s ORDER BY criada_em DESC", (status,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/ordens/resumo")
def get_ordens_resumo():
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_manutencao_por_equipamento")
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

@servico.get("/ordens/equipamento/<int:id_equipamento>/historico")
def get_ordens_historico_equipamento(id_equipamento):
    conexao = get_conexao_com_bd()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM vw_ordens_detalhadas WHERE equipamento_id = %s ORDER BY criada_em DESC", (id_equipamento,))
    registros = cursor.fetchall()
    conexao.close()
    return make_response(jsonify(registros), 200)

if __name__ == "__main__":
    servico.run(host="0.0.0.0", debug=True)
