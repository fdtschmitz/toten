from flask import Flask, request, jsonify, render_template, Response # type: ignore
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import io
import csv
import os

app = Flask(__name__)

DB_NAME = 'pesquisa.db'

opcoes_do_dia = [
    'arroz',
    'carne',
    'frango',
    'peixe',
    'feijao',
    'salada',
    'macarrao'
]

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
    """Rota para visualizar os relatórios com filtros de data."""
    # Captura os parâmetros da URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    view = request.args.get('view')

    hoje_dt = datetime.now()
    hoje_str = hoje_dt.strftime('%Y-%m-%d')
    
    # Lógica de definição das datas com base nos botões ou inputs
    if view == 'weekly':
        start_dt = hoje_dt - timedelta(days=7)
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = hoje_str
        periodo_str = f"Últimos 7 dias ({start_date} até {end_date})"
    elif start_date and end_date:
        periodo_str = f"Período: {start_date} até {end_date}"
    elif start_date: # Se o usuário colocar apenas a data de início (dia específico)
        end_date = start_date
        periodo_str = f"Data específica: {start_date}"
    else:
        # Padrão: visão diária de hoje
        start_date = hoje_str
        end_date = hoje_str
        periodo_str = f"Hoje ({hoje_str})"

    # Ajusta o horário para pegar o dia inteiro
    start_query = f"{start_date} 00:00:00"
    end_query = f"{end_date} 23:59:59"

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Busca com base no intervalo de datas
    cursor.execute(
        "SELECT * FROM respostas WHERE data_hora >= ? AND data_hora <= ?", 
        (start_query, end_query)
    )
    respostas_filtradas = cursor.fetchall()
    conn.close()
    
    # Processamento dos dados para o dashboard
    total = len(respostas_filtradas)
    
    metricas = {
        'total': total,
        'q1_gostei': sum(1 for r in respostas_filtradas if r['q1'] == 'gostei'),
        'q1_nao_gostei': sum(1 for r in respostas_filtradas if r['q1'] == 'nao_gostei'),

        'q2_gostei': sum(1 for r in respostas_filtradas if r['q2'] == 'gostei'),
        'q2_nao_gostei': sum(1 for r in respostas_filtradas if r['q2'] == 'nao_gostei'),

        'q3_gostei': sum(1 for r in respostas_filtradas if r['q3'] == 'gostei'),
        'q3_nao_gostei': sum(1 for r in respostas_filtradas if r['q3'] == 'nao_gostei'),
        
        'q4_comi_tudo': sum(1 for r in respostas_filtradas if r['q4'] == 'comi_tudo'),
        'q4_comi_pouco': sum(1 for r in respostas_filtradas if r['q4'] == 'comi_pouco'),
        'q4_nao_comi': sum(1 for r in respostas_filtradas if r['q4'] == 'nao_comi'),
        
        'rejeicoes': {}
    }

    contagem_rejeicoes = defaultdict(int)

    for r in respostas_filtradas:
        item_rejeitado = r['q6']
        # Filtra valores nulos, "nenhuma" ou "Nada_marcado"
        if item_rejeitado and item_rejeitado.lower() not in ['nenhuma', 'nada_marcado']:
            itens = [item.strip() for item in item_rejeitado.split(',')]
            for item in itens:
                if item and item.lower() != 'nada_marcado':
                    contagem_rejeicoes[item] += 1

    metricas['rejeicoes'] = {
        item: qtd for item, qtd in contagem_rejeicoes.items() if qtd > 0
    }

    return render_template(
        'dashboard.html', 
        metricas=metricas, 
        periodo_str=periodo_str, 
        start_date=start_date, 
        end_date=end_date
    )

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