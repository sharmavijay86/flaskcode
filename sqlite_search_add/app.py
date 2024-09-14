from flask import Flask, request, render_template, g
import sqlite3

app = Flask(__name__)
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER NOT NULL
            )
        ''')
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (name, email, age) VALUES (?, ?, ?)', (name, email, age))
        db.commit()
        return 'User added successfully!'
    return render_template('add_user.html')

@app.route('/search_user', methods=['GET'])
def search_user():
    name = request.args.get('name')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
    user = cursor.fetchone()
    return render_template('index.html', user=user)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
