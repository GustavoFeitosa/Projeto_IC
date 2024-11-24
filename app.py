from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração do app
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Alterar para algo mais seguro em produção

# Banco de Dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Tabela de pacientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    # Tabela de dados de saúde
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            pressao_arterial TEXT,
            frequencia_cardiaca INTEGER,
            exames TEXT,
            sintomas TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')
    conn.commit()
    conn.close()

# Rota inicial
@app.route('/')
def index():
    return redirect(url_for('login'))

# Cadastro de pacientes
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        senha_hash = generate_password_hash(senha)  # Criptografa a senha
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pacientes (nome, senha) VALUES (?, ?)', (nome, senha_hash))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('cadastro.html')

# Login de pacientes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, senha FROM pacientes WHERE nome = ?', (nome,))
        paciente = cursor.fetchone()
        conn.close()
        if paciente and check_password_hash(paciente[1], senha):
            session['paciente_id'] = paciente[0]
            return redirect(url_for('dados'))
        else:
            return "Login falhou. Verifique suas credenciais."
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('paciente_id', None)
    return redirect(url_for('login'))

# Inserir e visualizar dados de saúde
@app.route('/dados', methods=['GET', 'POST'])
def dados():
    if 'paciente_id' not in session:
        return redirect(url_for('login'))
    paciente_id = session['paciente_id']
    if request.method == 'POST':
        data = request.form['data']
        pressao_arterial = request.form['pressao_arterial']
        frequencia_cardiaca = request.form['frequencia_cardiaca']
        exames = request.form['exames']
        sintomas = request.form['sintomas']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dados_saude (paciente_id, data, pressao_arterial, frequencia_cardiaca, exames, sintomas)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (paciente_id, data, pressao_arterial, frequencia_cardiaca, exames, sintomas))
        conn.commit()
        conn.close()
        return redirect(url_for('dados'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_saude WHERE paciente_id = ?', (paciente_id,))
    dados = cursor.fetchall()
    conn.close()
    return render_template('dados.html', dados=dados)

# Visualização de dados pela equipe assistencial
@app.route('/equipe', methods=['GET'])
def equipe():
    if 'paciente_id' not in session or session.get('paciente_id') != 1:  # Restrição básica (alterar conforme necessário)
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_saude')
    todos_dados = cursor.fetchall()
    conn.close()
    return render_template('equipe.html', todos_dados=todos_dados)

# Inicialização do banco de dados
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
