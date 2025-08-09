from flask import Flask, render_template, request, session, redirect, url_for, flash, g
import flask_login, bcrypt, sqlite3, os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(os.environ.get("DB_FILE", "database.db"))
        db.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)
        db.commit()
    return db
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    user_agent = request.user_agent
    return render_template('index.html', user_agent=user_agent)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_agent = request.user_agent
        print(username, password, email, user_agent)
    user_agent = request.user_agent
    return render_template('login.html', user_agent=user_agent)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_agent = request.user_agent
        print(username, password, email)
    user_agent = request.user_agent
    return render_template('signup.html', user_agent=user_agent)
app.run(debug=True, port=6969)