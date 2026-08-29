# Dashboard - Refeitório Escolar

Um sistema web leve e responsivo desenvolvido em Python (Flask) para coletar, armazenar e analisar o nível de satisfação das crianças em um refeitório, utilizando um iPad para a coleta de respostas.

## 🚀 Funcionalidades

* **Coleta de Dados Estruturada:** Interface (API) preparada para receber as avaliações dos alunos via JSON e registrar no banco local com segurança.
* **Dashboard Interativo e Visual:** Painel administrativo gerado com `Chart.js` para visualização das métricas de aprovação diárias ou semanais.
* **Filtros de Período:** Visualize facilmente os dados do dia atual, últimos 7 dias, ou filtre por um intervalo de datas específico usando o calendário.
* **Exportação de Dados (CSV):** Exporte todos os registros em formato CSV com codificação amigável (UTF-8 com BOM) para abertura perfeita no Microsoft Excel.
* **Servidor Local de Alta Performance:** Utiliza o servidor WSGI `waitress` para operar com máxima eficiência e suporte a concorrência na rede local (Wi-Fi), garantindo estabilidade no uso pelos tablets.

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python, Flask, SQLite3
* **Front-end:** HTML5, CSS3, JavaScript (Chart.js)
* **Servidor WSGI:** Waitress

## ⚙️ Pré-requisitos

* Python 3.8 ou superior
* Gerenciador de pacotes `pip`

## 📦 Como Instalar e Rodar o Projeto

1. Clone este repositório ou faça o download dos arquivos.
2. Abra o terminal na pasta raiz do projeto.
3. (Opcional, porém recomendado) Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # Ativação no Linux/macOS:
   source venv/bin/activate
   # Ativação no Windows:
   venv\Scripts\activate
   ```
4. Instale as dependências contidas no arquivo `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
5. Inicie o servidor da aplicação:
   ```bash
   python app.py
   ```
6. O terminal exibirá o endereço IP da sua máquina na rede local (exemplo: `http://192.168.0.x:5000`).
7. Conecte o iPad na **mesma rede Wi-Fi** e acesse esse endereço pelo navegador (Safari/Chrome).

## 🗂️ Estrutura do Projeto

* `app.py` - Lógica principal de rotas, API, banco de dados e inicialização WSGI.
* `templates/index.html` - Interface de usuário servida para o iPad responder às perguntas (a ser incluída).
* `templates/dashboard.html` - Interface visual de dados e gráficos.
* `requirements.txt` - Dependências essenciais do projeto.
* `pesquisa.db` - Banco de dados local SQLite (gerado automaticamente na primeira execução).

