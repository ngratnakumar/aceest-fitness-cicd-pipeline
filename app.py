from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "aceest_fitness.db"

# Creating initial SQLite 
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS clients 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, age INTEGER, weight REAL)''')
    conn.commit()
    conn.close()

@app.before_request
def setup():
    init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    return f"<h1>ACEest Fitness Dashboard</h1><p>Total Clients: {len(clients)}</p>"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)