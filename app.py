from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for # type: ignore
from waitress import serve
from functools import wraps
import socket
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import io
import csv
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configurações de Segurança puxadas do .env
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_fallback')
app.permanent_session_lifetime = timedelta(days=365) # Evita que o totem deslogue no meio do dia
TOTEM_PASSWORD = os.environ.get('APP_PASSWORD', '12345').strip()

# Garante que a pasta 'data' exista para o volume do Docker
DB_DIR = 'data'
os.makedirs(DB_DIR, exist_ok=True)
DB_NAME = os.path.join(DB_DIR, 'pesquisa.db')

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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT, q6 TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- DECORADOR DE LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Captura tanto via JSON (Fetch) quanto via formulário comum
        dados = request.get_json() if request.is_json else request.form
        senha_digitada = dados.get('password', '').strip()
        
        if senha_digitada == TOTEM_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            
            if request.is_json:
                return jsonify({"sucesso": True, "redirect": url_for('index')}), 200
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({"sucesso": False, "erro": "Senha incorreta"}), 401
            return render_template('login.html', erro="Senha incorreta")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/salvar_pesquisa', methods=['POST'])
@login_required
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

@app.route('/dashboard')
@login_required
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
@login_required
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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online"}), 200

if __name__ == '__main__':
    init_db()
    serve(app, host='0.0.0.0', port=5000, threads=2)