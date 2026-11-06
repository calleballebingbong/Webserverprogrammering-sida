from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import pymysql

#$env:DB_PASSWORD = "psswrd"

app = Flask(__name__)
app.secret_key = 'secret_key'

def get_db_connection():
    return pymysql.connect (
        host='localhost',
        user='flask_app',
        password = os.environ['DB_PASSWORD'],
        database="webserver_db",
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

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

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                """
                SELECT username, password_hash
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            user = cursor.fetchone()
        finally:
            connection.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            return redirect(url_for('profile'))

        return render_template(
            'login.html',
            error="Invalid username or password."
            )
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_hash = generate_password_hash(request.form['password'])
        email = request.form.get('email', "")

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email)
                    VALUES (%s, %s, %s)
                    """,
                    (username, password_hash, email),
                )
                connection.commit()
        except pymysql.err.IntegrityError as error:
            connection.rollback()
            if error.args[0] != 1062:  # Duplicate entry error code
                raise
            return render_template(
                'register.html',
                error="Username already exists. Please choose a different username."
            )
        finally:
            connection.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    username = session['user']
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email FROM users
                WHERE username = %s
                """,
                (username,),
            )
            user = cursor.fetchone()
            if user is None:
                session.pop('user', None)
                return redirect(url_for('login'))
            cursor.execute(
                """
                SELECT id, title, body, created_at FROM forum_threads
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user['id'],),
            )
            posts = cursor.fetchall()
    finally:
        connection.close()

    return render_template('profile.html', username=username, email=user['email'] or '', posts=posts)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/threads', methods=['GET', 'POST'])
def threads():
    if request.method == 'POST' and 'user' not in session:
        return redirect(url_for('login'))

    error = None
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                title = request.form['title'].strip()
                body = request.form['body'].strip()

                if not title or not body:
                    error = "Please enter both a title and a post."
                else:
                    cursor.execute(
                        "SELECT id FROM users WHERE username = %s",
                        (session['user'],),
                    )
                    user = cursor.fetchone()

                    if user is None:
                        session.pop('user', None)
                        return redirect(url_for('login'))

                    cursor.execute(
                        """
                        INSERT INTO forum_threads (user_id, title, body)
                        VALUES (%s, %s, %s)
                        """,
                        (user['id'], title, body),
                    )
                    connection.commit()
                    return redirect(url_for('threads'))

            cursor.execute(
                """
                SELECT forum_threads.id, forum_threads.title,
                    forum_threads.body, forum_threads.created_at,
                    users.username
                FROM forum_threads
                JOIN users ON forum_threads.user_id = users.id
                ORDER BY forum_threads.created_at DESC
                """
            )
            thread_list = cursor.fetchall()

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return render_template(
        'threads.html',
        threads=thread_list,
        error=error,
    )

@app.route('/threads/<int:thread_id>/<slug>', methods=['GET', 'POST'])
def inthreads(thread_id, slug):
    if request.method == 'POST' and 'user' not in session:
        return redirect(url_for('login'))

    error = None
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT forum_threads.id, forum_threads.title,forum_threads.body,forum_threads.created_at,users.username
                FROM forum_threads
                Join users ON forum_threads.user_id = users.id
                WHERE forum_threads.id = %s
                """,
                (thread_id,),
            )
            thread = cursor.fetchone()

            if thread is None:
                abort(404)

            if request.method == 'POST':
                body = request.form.get('comment', '').strip()
                if not body:
                    error = "Please enter a comment."
                else:
                    cursor.execute(
                        "SELECT id FROM users WHERE username = %s",
                        (session['user'],),
                    )
                    user = cursor.fetchone()

                    if user is None:
                        session.pop('user', None)
                        return redirect(url_for('login'))

                    cursor.execute(
                        """
                        INSERT INTO forum_comments (thread_id, user_id, body)
                        VALUES (%s, %s, %s)
                        """,
                        (thread_id, user['id'], body),
                    )
                    connection.commit()
                    return redirect(
                        url_for(
                            'inthreads',
                            thread_id=thread_id,
                            slug=slug,
                        )
                    )

            cursor.execute(
                """
                SELECT forum_comments.body, forum_comments.created_at,users.username
                From forum_comments
                JOIN users ON forum_comments.user_id = users.id
                WHERE forum_comments.thread_id = %s
                ORDER BY forum_comments.created_at ASC
                """,
                (thread_id,),
            )
            comments = cursor.fetchall()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return render_template(
        'inthread.html',
        thread=thread,
        comments=comments,
        error=error,
    )


@app.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    if request.method == 'POST' and 'user' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                cursor.execute (
                    """
                    INSERT INTO guestbook_entries
                        (name, email, website, message)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        request.form['name'],
                        request.form.get('email', ''),
                        request.form.get('website', ''),
                        request.form['message']
                    ),
                )
                connection.commit()
                return redirect(url_for('guestbook'))
            cursor.execute(
                """
                SELECT id, name, email, website, message,
                    created_at AS timestamp
                FROM guestbook_entries
                ORDER BY id DESC
                """
            )
            entries = cursor.fetchall()
            for entry in entries:
                entry['comments'] = []

            cursor.execute(
                """
                SELECT entry_id, name, message, created_at AS timestamp
                FROM guestbook_comments
                ORDER BY id ASC
                """
            )
            comments = cursor.fetchall()

            entries_by_id = {entry['id']: entry for entry in entries}
            for comment in comments:
                entries_by_id[comment['entry_id']]['comments'].append(comment)

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return render_template('guestbook.html', entries=entries)

@app.route('/guestbook/<int:entry_id>/comment', methods=['POST'])
def ann_comment(entry_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO guestbook_comments (entry_id, name, message)
                VALUES (%s, %s, %s)
                """,
                (
                    entry_id,
                    request.form.get('comment_name'),
                    request.form.get('comment_message')
                )
            )
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return redirect('/guestbook')

if __name__ == '__main__':
    app.run(debug=True)



    