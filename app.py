from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Banco de Dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente TEXT NOT NULL,
            receita TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/receitas', methods=['GET', 'POST'])
def receitas():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        paciente = request.form['paciente']
        receita = request.form['receita']
        cursor.execute('INSERT INTO receitas (paciente, receita) VALUES (?, ?)', (paciente, receita))
        conn.commit()
    cursor.execute('SELECT * FROM receitas')
    receitas = cursor.fetchall()
    conn.close()
    return render_template('receitas.html', receitas=receitas)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
