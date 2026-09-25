from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret_key'

USER_FILE = 'users.json'

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def load_entries():
    try:
        with open('guestbook.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():  
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()

        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            return redirect(url_for('profile'))
        else:
            return "Invalid username or password."
    return """
    <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <button type="submit">Login</button>
    </form>
    """

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()

        if username in users:
            return "Username already exists."

        users[username] = {
            "password": generate_password_hash(password),
            "email": request.form.get('email', "")
        }

        save_users(users)
        return redirect(url_for('login'))

    return """
    <form method="post">
        Username: <input name="username"><br>
        Email: <input name="email"><br>
        Password: <input name="password" type="password"><br>
        <button type="submit">Register</button>
    </form>
    """

@app.route('/profile')
@login_required
def profile():
    username = session['user']
    users = load_users()
    email = users[username].get('email', "")
    return f"welcome {username}! Your email is {email}."

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    entries = load_entries()

    if request.method == 'POST':
        new_entry = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'message': request.form.get('message'),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"New entry from {new_entry['name']}: {new_entry}")
        entries.insert(0, new_entry)

        with open('guestbook.json', 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=4)

    return render_template('guestbook.html', entries=entries)

@app.route('/guestbook/<int:entry_index>/comment', methods=['POST'])
def ann_comment(entry_index):
    entries = load_entries()

    if 0 <= entry_index < len(entries):
        comment = {
            'name': request.form.get('comment_name'),
            'message': request.form.get('comment_message'),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if 'comments' not in entries[entry_index]:
            entries[entry_index]['comments'] = []

        entries[entry_index]['comments'].append(comment)

        with open('guestbook.json', 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=4)
    return redirect('/guestbook')

if __name__ == '__main__':
    app.run(debug=True)



    