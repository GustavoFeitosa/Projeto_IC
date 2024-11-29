from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_weasyprint import HTML, render_pdf
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração do app
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

# Códigos de acesso fornecidos pelo administrador
CODIGO_ACESSO_EQUIPE = 'hcp1234'
CODIGO_ACESSO_PACIENTE = 'pac1234'

# Banco de Dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL CHECK(tipo_usuario IN ('paciente', 'equipe'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pressao_sistolica INTEGER CHECK(pressao_sistolica BETWEEN 50 AND 330),
            pressao_diastolica INTEGER CHECK(pressao_diastolica BETWEEN 10 AND 230),
            frequencia_cardiaca INTEGER CHECK(frequencia_cardiaca BETWEEN 30 AND 220),
            peso REAL CHECK(peso BETWEEN 20 AND 300),
            saturacao_oxigenio INTEGER CHECK(saturacao_oxigenio BETWEEN 51 AND 100),
            glicemia INTEGER CHECK(glicemia BETWEEN 11 AND 500),
            sintomas TEXT,
            exames TEXT,
            receita TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        tipo_usuario = request.form['tipo_usuario']
        senha_hash = generate_password_hash(senha)
        codigo = request.form.get('codigo', '')  # Código da equipe
        codigo_paciente = request.form.get('codigo_paciente', '')  # Código do paciente

        # Validação do código de acesso
        if tipo_usuario == 'paciente' and codigo_paciente != 'pac123':
            flash('Código do paciente inválido.', 'error')
            return redirect(url_for('cadastro'))

        if tipo_usuario == 'equipe' and codigo != 'hcp1234':
            flash('Código de acesso para equipe inválido.', 'error')
            return redirect(url_for('cadastro'))

        # Caso o código seja válido, cria o usuário no banco
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pacientes (nome, senha, tipo_usuario) VALUES (?, ?, ?)',
                       (nome, senha_hash, tipo_usuario))
        conn.commit()
        conn.close()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/termo')
def termo():
    return render_template('termo.html')

@app.route('/politica')
def politica():
    return render_template('politica.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('_flashes', None)  # Remover mensagens antigas ao acessar a página
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

@app.route('/logout')
def logout():
    session.pop('paciente_id', None)
    session.pop('tipo_usuario', None)
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/dados', methods=['GET', 'POST'])
def dados():
    if 'paciente_id' not in session or session.get('tipo_usuario') != 'paciente':
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login'))
    paciente_id = session['paciente_id']
    if request.method == 'POST':
        try:
            pressao_sistolica = int(request.form['pressao_sistolica']) if request.form['pressao_sistolica'] else None
            pressao_diastolica = int(request.form['pressao_diastolica']) if request.form['pressao_diastolica'] else None
            frequencia_cardiaca = int(request.form['frequencia_cardiaca']) if request.form['frequencia_cardiaca'] else None
            peso = float(request.form['peso']) if request.form['peso'] else None
            saturacao_oxigenio = int(request.form['saturacao_oxigenio']) if request.form['saturacao_oxigenio'] else None
            glicemia = int(request.form['glicemia']) if request.form['glicemia'] else None
            sintomas = request.form['sintomas']
            exames = request.form['exames']
            receita = request.form['receita']

            if not any([pressao_sistolica, pressao_diastolica, frequencia_cardiaca, peso, saturacao_oxigenio, glicemia, sintomas, exames, receita]):
                flash('Erro: Preencha pelo menos um campo.', 'error')
                return redirect(url_for('dados'))

            if (pressao_sistolica and (pressao_sistolica < 50 or pressao_sistolica > 330)) or \
               (pressao_diastolica and (pressao_diastolica < 10 or pressao_diastolica > 230)) or \
               (frequencia_cardiaca and (frequencia_cardiaca < 30 or frequencia_cardiaca > 220)) or \
               (peso and (peso < 20 or peso > 300)) or \
               (saturacao_oxigenio and (saturacao_oxigenio < 51 or saturacao_oxigenio > 100)) or \
               (glicemia and (glicemia < 11 or glicemia > 500)):
                flash('Erro: Fora da margem aceita.', 'error')
                return redirect(url_for('dados'))

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dados_saude (
                    paciente_id, pressao_sistolica, pressao_diastolica, frequencia_cardiaca,
                    peso, saturacao_oxigenio, glicemia, sintomas, exames, receita
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (paciente_id, pressao_sistolica, pressao_diastolica, frequencia_cardiaca, peso,
                  saturacao_oxigenio, glicemia, sintomas, exames, receita))
            conn.commit()
            conn.close()
            flash('Dados inseridos com sucesso!', 'success')
            return redirect(url_for('dados'))
        except ValueError:
            flash('Erro: Valores inválidos.', 'error')
            return redirect(url_for('dados'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_saude WHERE paciente_id = ? ORDER BY data_hora DESC', (paciente_id,))
    dados = cursor.fetchall()
    conn.close()
    return render_template('dados.html', dados=dados)

@app.route('/historico_pdf', methods=['GET'])
def historico_pdf():
    if 'paciente_id' not in session or session.get('tipo_usuario') != 'paciente':
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('login'))

    paciente_id = session['paciente_id']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_saude WHERE paciente_id = ? ORDER BY data_hora DESC', (paciente_id,))
    dados = cursor.fetchall()
    conn.close()

    html = render_template('historico_pdf.html', dados=dados)
    return render_pdf(HTML(string=html))

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
               dados_saude.peso, dados_saude.saturacao_oxigenio, dados_saude.glicemia,
               dados_saude.sintomas, dados_saude.exames, dados_saude.receita
        FROM dados_saude
        INNER JOIN pacientes ON pacientes.id = dados_saude.paciente_id
        ORDER BY pacientes.nome, dados_saude.data_hora DESC
    ''')
    todos_dados = cursor.fetchall()

    dados_formatados = []
    for dado in todos_dados:
        dado = [d if d is not None else '-' for d in dado]
        critico = {
            "pressao_sistolica": dado[2] != '-' and (int(dado[2]) > 150 or int(dado[2]) < 85),
            "pressao_diastolica": dado[3] != '-' and (int(dado[3]) > 100 or int(dado[3]) < 40),
            "frequencia_cardiaca": dado[4] != '-' and (int(dado[4]) > 100 or int(dado[4]) < 45),
            "peso": dado[5] != '-' and (float(dado[5]) < 20 or float(dado[5]) > 300),
            "saturacao_oxigenio": dado[6] != '-' and (int(dado[6]) < 90),
            "glicemia": dado[7] != '-' and (int(dado[7]) > 200 or int(dado[7]) < 70)
        }
        dados_formatados.append((dado, critico))

    conn.close()
    return render_template('equipe.html', dados_formatados=dados_formatados)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
