from flask import Flask, render_template, request, redirect, url_for, session, flash
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
            senha TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL CHECK(tipo_usuario IN ('paciente', 'equipe'))
        )
    ''')
    # Tabela de dados de saúde
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pressao_sistolica INTEGER CHECK(pressao_sistolica BETWEEN 40 AND 330),
            pressao_diastolica INTEGER CHECK(pressao_diastolica BETWEEN 10 AND 230),
            frequencia_cardiaca INTEGER CHECK(frequencia_cardiaca BETWEEN 30 AND 220),
            peso REAL CHECK(peso BETWEEN 20 AND 300),
            receita TEXT,
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
        tipo_usuario = request.form['tipo_usuario']
        senha_hash = generate_password_hash(senha)  # Criptografa a senha

        # Validações
        if not nome or not senha or not tipo_usuario:
            flash('Todos os campos são obrigatórios!', 'error')
            return redirect(url_for('cadastro'))

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO pacientes (nome, senha, tipo_usuario) VALUES (?, ?, ?)',
                           (nome, senha_hash, tipo_usuario))
            conn.commit()
        except sqlite3.Error as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
        finally:
            conn.close()

        flash('Cadastro realizado com sucesso!', 'success')
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
        cursor.execute('SELECT id, senha, tipo_usuario FROM pacientes WHERE nome = ?', (nome,))
        paciente = cursor.fetchone()
        conn.close()
        if paciente and check_password_hash(paciente[1], senha):
            session['paciente_id'] = paciente[0]
            session['tipo_usuario'] = paciente[2]
            if paciente[2] == 'equipe':
                return redirect(url_for('equipe'))
            else:
                return redirect(url_for('dados'))
        else:
            flash('Nome ou senha incorretos.', 'error')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('paciente_id', None)
    session.pop('tipo_usuario', None)
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('login'))

# Inserir e visualizar dados de saúde (paciente)
@app.route('/dados', methods=['GET', 'POST'])
def dados():
    if 'paciente_id' not in session or session.get('tipo_usuario') != 'paciente':
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login'))
    paciente_id = session['paciente_id']
    if request.method == 'POST':
        try:
            pressao_sistolica = int(request.form['pressao_sistolica'])
            pressao_diastolica = int(request.form['pressao_diastolica'])
            frequencia_cardiaca = int(request.form['frequencia_cardiaca'])
            peso = float(request.form['peso'])
            receita = request.form['receita']

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dados_saude (paciente_id, pressao_sistolica, pressao_diastolica, frequencia_cardiaca, peso, receita)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (paciente_id, pressao_sistolica, pressao_diastolica, frequencia_cardiaca, peso, receita))
            conn.commit()
            flash('Dados inseridos com sucesso!', 'success')
        except ValueError:
            flash('Valores inválidos. Confira os campos e tente novamente.', 'error')
        finally:
            conn.close()
        return redirect(url_for('dados'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_saude WHERE paciente_id = ? ORDER BY data_hora DESC', (paciente_id,))
    dados = cursor.fetchall()
    conn.close()
    return render_template('dados.html', dados=dados)

# Visualização dos dados pela equipe assistencial
@app.route('/equipe', methods=['GET'])
def equipe():
    if 'paciente_id' not in session or session.get('tipo_usuario') != 'equipe':
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pacientes.nome, dados_saude.data_hora, dados_saude.pressao_sistolica,
               dados_saude.pressao_diastolica, dados_saude.frequencia_cardiaca,
               dados_saude.peso, dados_saude.receita
        FROM dados_saude
        INNER JOIN pacientes ON pacientes.id = dados_saude.paciente_id
        ORDER BY pacientes.nome, dados_saude.data_hora DESC
    ''')
    todos_dados = cursor.fetchall()
    conn.close()
    return render_template('equipe.html', todos_dados=todos_dados)

# Inicialização do banco de dados
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
