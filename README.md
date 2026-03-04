# Sistema de Gestão de Avarias - Transbirday

O **Sistema de Gestão de Avarias** foi desenvolvido sob demanda para a transportadora Transbirday, com o objetivo de registrar, gerenciar e acompanhar incidentes e avarias de cargas ocorridas durante o processo de transporte logística.

## 📋 Funcionalidades Principais

* **Cadastro e Gestão Inicial de Avarias:** O sistema possibilita registrar notas fiscais, motoristas envolvidos, transportadoras parcerias, e os produtos que sofreram alguma avaria.
* **Fotos e Evidências:** É possível anexar imagens que comprovem os danos nos produtos diretamente durante a abertura do registro.
* **Acompanhamento de Status:** O fluxo de uma avaria e a sua decisão passam por processos definidos (Em Aberto, Decisão, Aguardando Devolução, Em Rota, Finalizada).
* **Gestão de Cadastros Base (CRUDs):** Controle de Condutores (CPFs únicos, ativação/inativação), Veículos (frotas, agregados e terceiros parcerias), Clientes, Produtos (geração de código de controle) e Centros de Distribuição para logística reversa.
* **Níveis de Acesso:** Há separação de papéis entre *Gestores* (Acesso web full) e perfis *Operacionais* (Focados no report mobile/PWA). 
* **Geração de Relatórios em PDF:** Acompanhamento via PDF (ex: Relatório de Usuários do Sistema).
* **Sincronismo/Integrações Básicas:** Consultas automáticas de CNPJ pela BrasilAPI no cadastro de clientes.

---

## 🚀 Tecnologias e Stacks (Tech Stack)

Este sistema baseia-se no ecossistema Python com o framework Django para desenvolvimento ágil e seguro.

* **Back-end e Core Logic:** Python 3.x e **Django 6.0**
* **Frontend:** Templates HTML renderizados no lado do servidor utilizando o Django Templating Language (DTL). Estilizados com Vanilla CSS / Bootstrap 5 (inferido).
* **Banco de Dados Local:** SQLite3 (Para desenvolvimento / prototipagem `db.sqlite3`).

### 📦 Principais Bibliotecas e Dependências (`requirements.txt`)

* **Django (6.0.1)** - Framework web principal.
* **djangorestframework (3.16)** - Para viabilizar criação de APIs e serialização de dados (módulo `app_api`).
* **django-pwa (2.0.1)** - Para possibilitar que a aplicação se comporte como um aplicativo móvel instalável (Progressive Web App).
* **pillow (12.1.0)** - Responsável pelo poderoso redimensionamento e tratamento de imagens no envio de arquivos e fotos das avarias.
* **reportlab (4.4.6)** - Utilizado para a confecção dinâmica de arquivos e relatórios `.pdf`.
* **requests (2.32.5)** - Facilita as chamadas HTTP, como nas chamadas à BrasilAPI.
* **python-decouple (3.8)** - Para tratamento e segurança das variáveis de ambiente / `.env`.
* **whitenoise (6.11.0)** - Usado para servir arquivos estáticos (CSS, JS) de forma simplificada sem intermédio de Nginx / Apache em ambientes standalone.

---

## 📱 Suporte a PWA (Progressive Web App)

O sistema foi preparado para rodar como um **PWA**, focando usuários operacionais (Motoristas, Conferentes) que precisam acessar o sistema pelo celular no pátio ou na rua.

* Graças ao pacote `django-pwa`, existe um **Service Worker** e um **Manifesto PWA** acoplados.
* Ao abrir a URL do sistema no celular via Chrome/Safari, ele oferecerá a opção "Adicionar à Tela Inicial", instalando como um app nativo.
* Contém cache básico de arquivos para proporcionar a casca do app e visualização offline do menu / tela amigável caso momentaneamente caia a conexão.
* Verificação de rota de offline dedicada em `/offline/`.

---

## ⚙️ Manual de Instalação Local

Para rodar este ambiente em sua própria máquina para desenvolvimento, siga o roteiro abaixo:

**Pré-requisitos:** ter o Pytbhon 3.10+ (ou compatível com Django 6.x) instalado.

1. **Clone o repositório ou navegue até a pasta do projeto:**
   ```bash
   cd Avarias_Projeto
   ```

2. **Crie e ative um Ambiente Virtual (Virtual Environment):**
   * No Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * No Linux/Mac:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Realize as Migrações do Banco de Dados:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crie o Superusuário (Gestor Master):**
   ```bash
   python manage.py createsuperuser
   ```
   *(Siga os passos e insira usuario, email e senha)*.

6. **Inicie o Servidor Local de Desenvolvimento:**
   ```bash
   python manage.py runserver
   ```
   *Acesse `http://127.0.0.1:8000/` no seu navegador.*

---

## 💻 Principais Comandos Terminal (Bash / PowerShell)

Um cheatsheet rápido com os comandos mais utilizados no fluxo de desenvolvimento com Django:

| Ação | Comando |
| :--- | :--- |
| **Ativar pasta virtual (Windows)** | `.\venv\Scripts\activate` |
| **Ativar pasta virtual (Mac/Linux)** | `source venv/bin/activate` |
| **Startar Servidor** | `python manage.py runserver` |
| **Instalar nova biblioteca** | `pip install nome-da-biblioteca` |
| **Gerar lista atualizada de dependências** | `pip freeze > requirements.txt` |
| **Preparar Migrações (após alterar DB)** | `python manage.py makemigrations` |
| **Aplicar Migrações** | `python manage.py migrate` |
| **Criar Usuário Master** | `python manage.py createsuperuser` |
| **Coletar arquivos Estáticos (Produção)**| `python manage.py collectstatic` |
| **Acessar o Terminal shell do Django** | `python manage.py shell` |
