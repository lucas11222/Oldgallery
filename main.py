from flask import Flask, render_template, request, session, redirect, url_for, flash
import json, os

app = Flask(__name__)
app.secret_key = 'heres_the_secret_key'
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({'users': {}}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    user_agent = request.user_agent
    return render_template('index.html', user_agent=user_agent)
@app.route('/login', methods=['GET', 'POST'])
def login():
    user_agent = request.user_agent
    return render_template('login.html', user_agent=user_agent)
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    user_agent = request.user_agent
    return render_template('signin.html', user_agent=user_agent)
app.run(debug=True, port=6969)