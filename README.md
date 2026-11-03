# Dashboard & Totem de Pesquisa de Satisfação - Refeitório Escolar

Um sistema web leve, responsivo e seguro desenvolvido em Python (Flask + Waitress) para coletar, armazenar e analisar o nível de satisfação das crianças em um refeitório escolar. O sistema foi projetado para rodar em um iPad (modo Totem / Kiosk em tela cheia) e conta com um painel administrativo com gráficos e exportação de relatórios.

## 🚀 Funcionalidades

* **Totem de Coleta Interativo:** Interface lúdica com pictogramas/emojis grandes e navegação por timeline, otimizada para iPad e telas de toque.
* **Autenticação e Segurança:** Proteção da aplicação e do painel por senha de acesso com sessão persistente via cookie assinado.
* **Dashboard de Métricas:** Painel gerencial com suporte a gráficos (`Chart.js`) e filtros temporais (diário, semanal ou por intervalo customizado).
* **Exportação CSV:** Download dos registros consolidados formatados para leitura direta no Microsoft Excel / Google Sheets (UTF-8 com BOM e delimitador `;`).
* **Endpoint de Uptime / Health Check:** Rota `/health` pronta para integração com serviços de monitoramento (Uptime Kuma, n8n, etc.).
* **Pronto para Produção em Docker:** Arquitetura isolada via Docker e Docker Compose com servidor WSGI `waitress` de alta performance.
* **Persistência Segura de Dados:** Mapeamento de volume para garantir a integridade da base SQLite (`pesquisa.db`) entre reinícios do contêiner.

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python 3.11, Flask, Waitress, `python-dotenv`
* **Banco de Dados:** SQLite3
* **Front-end:** HTML5, CSS3, JavaScript (Google Fonts Montserrat, Chart.js)
* **Infraestrutura:** Docker, Docker Compose, Nginx (Proxy Reverso), Certbot (SSL)

---

## ⚙️ Configuração do Ambiente (`.env`)

Antes de iniciar a aplicação, crie um arquivo chamado `.env` na raiz do projeto com as seguintes chaves de configuração:

```env
SECRET_KEY=sua_chave_criptografica_gerada
APP_PASSWORD=sua_senha_de_acesso_ao_totem
```

> 💡 **Dica para gerar a `SECRET_KEY`:**  
> Execute o seguinte comando no terminal para criar uma chave aleatória forte:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## 🐳 Execução via Docker (Recomendado)

### Pré-requisitos
* Docker instalado
* Docker Compose (V2)

### Passo a Passo

1. Garanta que o arquivo `.env` esteja preenchido.
2. Suba o contêiner em segundo plano:
   ```bash
   docker compose up -d --build
   ```
3. O contêiner subirá isolado na porta **5005** do host local (`127.0.0.1:5005`), pronto para ser consumido pelo Nginx.

---

## 🌐 Configuração do Proxy Reverso (Nginx)

Para expor a aplicação com HTTPS sob o subdomínio `totem.coreeschool.com.br`, adicione o seguinte bloco de configuração ao seu Nginx (ex: `/etc/nginx/sites-available/totem.coreeschool.com.br`):

```nginx
server {
    listen 80;
    server_name totem.coreeschool.com.br;

    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Após recarregar o Nginx (`sudo systemctl reload nginx`), gere o certificado SSL com o Certbot:
```bash
sudo certbot --nginx -d totem.coreeschool.com.br
```

---

## 💻 Desenvolvimento / Execução Local Sem Docker

Caso prefira rodar diretamente na sua máquina local para desenvolvimento:

1. Crie e ative um ambiente virtual Python:
   ```bash
   python -m venv venv
   # Linux/macOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o servidor:
   ```bash
   python app.py
   ```
4. Acesse no navegador: `http://localhost:5000` ou pelo IP local exibido no terminal.

---

## 🗂️ Estrutura do Projeto

```text
pesquisa_satisfacao/
├── app.py                  # Servidor Flask/Waitress, rotas, autenticação e API
├── Dockerfile              # Imagem base Python 3.11 slim
├── docker-compose.yml      # Mapeamento de volume e porta (5005 -> 5000)
├── requirements.txt        # Dependências (Flask, Waitress, python-dotenv)
├── .env                    # Variáveis de ambiente (ignorado no Git)
├── data/                   # Pasta persistida via volume
│   └── pesquisa.db         # Banco de dados SQLite
├── static/
│   └── img/
│       └── logo.png        # Logo exibido na interface do totem
└── templates/
    ├── index.html          # Form de pesquisa (iPad / Kiosk)
    ├── dashboard.html      # Painel de relatórios e métricas
    └── login.html          # Tela de acesso autenticado
```