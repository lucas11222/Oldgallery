from flask import Flask, render_template, request, session, redirect, url_for, flash, g, Response
import flask_login, bcrypt, sqlite3, os, secrets
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

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
                username TEXT NOT NULL,
                computer_name TEXT PRIMARY KEY,
                os TEXT NOT NULL,
                ram INTEGER NOT NULL,
                cpu TEXT NOT NULL,
                gpu TEXT NOT NULL,
                storage INTEGER NOT NULL
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
        user.id = username
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

#@app.route('/example')
#@flask_login.login_required
#def example():
#    return "youre logged in! :D"

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash("you must be logged in to access this page :(", "error")
    return redirect("/login")

app.run(debug=True, port=6969)