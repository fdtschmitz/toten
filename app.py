from flask import Flask, request, jsonify, render_template, Response
import sqlite3
from datetime import datetime
import io
import csv
import os

app = Flask(__name__)

DB_NAME = 'pesquisa.db'

def init_db():
    """Cria o banco de dados e a tabela se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Estrutura preparada para receber as 6 perguntas e a data/hora exata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            q4 TEXT,
            q5 TEXT,
            q6 TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Rota que serve a interface do iPad."""
    return render_template('index.html')

@app.route('/api/salvar_pesquisa', methods=['POST'])
def salvar_pesquisa():
    """Rota que recebe o JSON do frontend e grava no SQLite."""
    dados = request.get_json()
    
    if not dados:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    # Captura a data e hora do momento da resposta
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extrai os valores das perguntas (retorna None se a chave não existir)
    q1 = dados.get('q1')
    q2 = dados.get('q2')
    q3 = dados.get('q3')
    q4 = dados.get('q4')
    q5 = dados.get('q5')
    q6 = dados.get('q6') # Pode vir como 'nenhuma' se a criança pulou pela lógica da Q5

    # Gravação no banco de dados usando placeholders (?) para segurança
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO respostas (data_hora, q1, q2, q3, q4, q5, q6)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data_hora, q1, q2, q3, q4, q5, q6))
    
    conn.commit()
    conn.close()

    return jsonify({"status": "sucesso"}), 201

# ... (mantenha os imports e o código anterior do app.py) ...

@app.route('/dashboard')
def dashboard():
    """Rota para visualizar os relatórios diários."""
    # Pega a data de hoje no formato YYYY-MM-DD
    hoje = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_NAME)
    # Permite acessar as colunas pelo nome (ex: linha['q1'])
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Busca apenas as respostas de hoje usando LIKE
    cursor.execute("SELECT * FROM respostas WHERE data_hora LIKE ?", (f"{hoje}%",))
    respostas_hoje = cursor.fetchall()
    conn.close()
    
    # Processamento dos dados para o dashboard
    total = len(respostas_hoje)
    
    metricas = {
        'total': total,
        'q1_gostei': sum(1 for r in respostas_hoje if r['q1'] == 'gostei'),
        'q1_nao_gostei': sum(1 for r in respostas_hoje if r['q1'] == 'nao_gostei'),
        
        'q4_comi_tudo': sum(1 for r in respostas_hoje if r['q4'] == 'comi_tudo'),
        'q4_comi_pouco': sum(1 for r in respostas_hoje if r['q4'] == 'comi_pouco'),
        'q4_nao_comi': sum(1 for r in respostas_hoje if r['q4'] == 'nao_comi'),
        
        # Contagem das preparações rejeitadas (ignorando quando a resposta for 'nenhuma' ou vazia)
        'rejeicoes': {}
    }

    for r in respostas_hoje:
        item_rejeitado = r['q6']
        if item_rejeitado and item_rejeitado != 'nenhuma':
            metricas['rejeicoes'][item_rejeitado] = metricas['rejeicoes'].get(item_rejeitado, 0) + 1

    return render_template('dashboard.html', metricas=metricas, data_hoje=datetime.now().strftime('%d/%m/%Y'))

@app.route('/exportar_csv')
def exportar_csv():
    """Rota para gerar e baixar o arquivo CSV com todos os dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Busca todas as respostas ordenadas das mais recentes para as mais antigas
    cursor.execute("SELECT * FROM respostas ORDER BY data_hora DESC")
    respostas = cursor.fetchall()
    
    # Captura o nome das colunas da tabela
    colunas = [descricao[0] for descricao in cursor.description]
    conn.close()

    # Usamos o StringIO para criar um buffer de texto em memória
    si = io.StringIO()
    # Usamos ponto e vírgula como delimitador pois o Excel em português lê melhor assim
    cw = csv.writer(si, delimiter=';') 
    
    # Escreve a linha de cabeçalho
    cw.writerow(colunas)
    # Escreve todas as linhas de dados
    cw.writerows(respostas)
    
    # Prepara a resposta HTTP forçando o download do arquivo
    output = si.getvalue()
    # O encode 'utf-8-sig' garante que caracteres com acento (BOM) abram corretamente no Excel
    return Response(
        output.encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=relatorio_pesquisa.csv"}
    )

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)