from flask import Flask, render_template, request, session, redirect, url_for, flash, g, send_from_directory
import flask_login, bcrypt, sqlite3, os, secrets
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
from werkzeug.utils import secure_filename

# thanks csd4ni3l
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(os.environ.get("DB_FILE", "database.db"))
        db.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Computers (
                email TEXT NOT NULL,
                computer_name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                os TEXT NOT NULL,
                ram INTEGER NOT NULL,
                cpu TEXT NOT NULL,
                gpu TEXT NOT NULL,
                storage INTEGER NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Servers (
                email TEXT NOT NULL,
                server_name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                os TEXT NOT NULL,
                ram INTEGER NOT NULL,
                cpu TEXT NOT NULL,
                gpu TEXT NOT NULL,
                storage INTEGER NOT NULL,
                ssh INTEGER NOT NULL,
                url INTEGER NOT NULL
            )
        """)
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_id):
    user = User()
    user.id = user_id
    return user

@app.route('/')
def index():
    user_agent = request.user_agent
    logged_in = flask_login.current_user.is_authenticated
    return render_template('index.html', user_agent=user_agent, logged_in=logged_in)

@flask_login.login_required
@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/dashboard/computers')
@flask_login.login_required
def dashboard():
    cur = get_db().cursor()
    email = flask_login.current_user.id
    cur.execute("SELECT computer_name, description, os, ram, cpu, gpu, storage FROM Computers WHERE email = ?", (email,))
    rows = cur.fetchall()
    return render_template('computers.html', rows=rows)

@app.route('/dashboard/add_computer', methods=['POST'])
@flask_login.login_required
def add_computer():
    data = request.form
    computer_name = data.get('computer-name')
    description = data.get('computer-description')
    os = data.get('computer-os')
    ram = data.get('computer-ram')
    cpu = data.get('computer-cpu')
    gpu = data.get('computer-gpu')
    storage = data.get('computer-storage')
    cur = get_db().cursor()
    email = flask_login.current_user.id
    cur.execute("SELECT 1 FROM Computers WHERE email = ? AND computer_name = ?", (email, computer_name))
    if cur.fetchone():
        flash("A computer with this name already exists :(", "error")
        cur.close()
        return redirect(url_for('computers'))
    cur.execute("INSERT INTO Computers (email, computer_name, description, os, ram, cpu, gpu, storage) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (email, computer_name, description, os, ram, cpu, gpu, storage))
    get_db().commit()
    cur.close()
    flash("computer added successfully :D", "success")
    return redirect(url_for('dashboard'))

@app.route('/dashboard/remove_computer', methods=['GET'])
@flask_login.login_required
def remove_computer():
    cur = get_db().cursor()
    computer_name = request.args.get('name')
    email = flask_login.current_user.id
    cur.execute("DELETE FROM Computers WHERE computer_name = ? AND email = ?",(computer_name, email))
    get_db().commit()
    cur.close()
    return redirect(url_for('dashboard'))

@app.route('/dashboard/servers')
@flask_login.login_required
def servers():
    cur = get_db().cursor()
    email = flask_login.current_user.id
    cur.execute("SELECT server_name, description, os, ram, cpu, gpu, storage FROM Servers WHERE email = ?", (email,))
    rows = cur.fetchall()
    return render_template('servers.html', rows=rows)

@app.route('/dashboard/add_Servers', methods=['POST'])
@flask_login.login_required
def add_servers():
    data = request.form
    server_name = data.get('Server-name')
    description = data.get('Server-description')
    os = data.get('Server-os')
    ram = data.get('Server-ram')
    cpu = data.get('Server-cpu')
    gpu = data.get('Server-gpu')
    storage = data.get('Server-storage')
    ssh = data.get('Server-ssh')
    url = data.get('Server-url')
    cur = get_db().cursor()
    email = flask_login.current_user.id
    cur.execute("SELECT 1 FROM Server WHERE email = ? AND server_name = ?", (email, server_name))
    if cur.fetchone():
        flash("A computer with this name already exists :(", "error")
        cur.close()
        return redirect(url_for('servers'))
    cur.execute("INSERT INTO Server (email, server_name, description, os, ram, cpu, gpu, storage, ssh, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (email, server_name, description, os, ram, cpu, gpu, storage, ssh, url))
    get_db().commit()
    cur.close()
    flash("server added successfully :D", "success")
    return redirect(url_for('servers'))

@app.route('/dashboard/remove_Servers', methods=['GET'])
@flask_login.login_required
def remove_server():
    cur = get_db().cursor()
    server_name = request.args.get('name')
    email = flask_login.current_user.id
    cur.execute("DELETE FROM Servers WHERE server_name = ? AND email = ?",(server_name, email))
    get_db().commit()
    cur.close()
    flash("server deleted successfully :(", "success")
    return redirect(url_for('servers'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        user_agent = data.get('user_agent')
        cur = get_db().cursor()
        cur.execute("SELECT password, password_salt, user_agent FROM Users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            cur.close()
            flash("unauthorized :(", "error")
            return render_template('login.html', user_agent=user_agent)
        hashed_password, salt, user_agent_db = row
        if user_agent_db != user_agent:
            cur.close()
            flash("unauthorized :(", "error")
            return render_template('login.html', user_agent=user_agent)
        if secrets.compare_digest(bcrypt.hashpw(password.encode(), salt.encode()), hashed_password.encode()):
            cur.close()
            user = User()
            user.id = email
            flask_login.login_user(user, remember=True)
            flash("logged in successfully :D", "success")
            return render_template('index.html', user_agent=user_agent)
        else:
            cur.close()
            flash("incorrect password :(", "error")
            return render_template('login.html', user_agent=user_agent)
    user_agent = request.user_agent
    logged_in = flask_login.current_user.is_authenticated
    if logged_in:
        flash("you are already logged in :D", "success")
        return redirect(url_for('index'))
    return render_template('login.html', user_agent=user_agent)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_agent = request.user_agent.string
        cur = get_db().cursor()
        cur.execute("SELECT username FROM Users WHERE username = ?", (username,))
        if cur.fetchone():
            flash("an account with this username already exists :(", "error")
            return render_template('signup.html', user_agent=user_agent)
        cur.execute("SELECT email FROM Users WHERE email = ?", (email,))
        if cur.fetchone():
            flash("an account with this email already exists :(", "error")
            return render_template('signup.html', user_agent=user_agent)
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        cur.execute("INSERT INTO Users (username, email, password, user_agent, password_salt) VALUES (?, ?, ?, ?, ?)", (username, email, hashed_password.decode(), user_agent, salt.decode()))
        get_db().commit()
        cur.close()
        user = User()
        user.id = email
        flask_login.login_user(user, remember=True)
        flash("signed up successfully :D", "success")
        return render_template('index.html', user_agent=user_agent)
    user_agent = request.user_agent
    logged_in = flask_login.current_user.is_authenticated
    if logged_in:
        flash("you are already logged in :D", "success")
        return redirect(url_for('index'))
    return render_template('signup.html', user_agent=user_agent)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    user_agent = request.user_agent.string
    flash("log out :(", "success")
    return render_template('index.html', user_agent=user_agent)

@flask_login.login_required
@app.route('/delete_account', methods=['POST'])
def delete_account():
    data = request.form
    password = data.get('password')
    user_agent = request.user_agent.string
    cur = get_db().cursor()
    cur.execute("SELECT password, password_salt FROM Users WHERE email = ?", (flask_login.current_user.id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        flash("unauthorized :(", "error")
        return render_template('login.html', user_agent=user_agent)
    hashed_password, salt = row
    if secrets.compare_digest(bcrypt.hashpw(password.encode(), salt.encode()), hashed_password.encode()):
        cur.execute("DELETE FROM Users WHERE email = ?", (flask_login.current_user.id,))
        cur.execute("DELETE FROM Servers WHERE email = ?",(flask_login.current_user.id,))
        cur.execute("DELETE FROM Computers WHERE email = ?",(flask_login.current_user.id,))
        get_db().commit()
        cur.close()
        flask_login.logout_user()
        flash("account deleted successfully :(", "success")
        return render_template('index.html', user_agent=user_agent)
    else:
        cur.close()
        flash("incorrect password :(", "error")
        return render_template('settings.html')

#@app.route('/example')
#@flask_login.login_required
#def example():
#    return "youre logged in! :D"

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash("you must be logged in to access this page :(", "error")
    return redirect("/login")

app.run(debug=True, port=6969)