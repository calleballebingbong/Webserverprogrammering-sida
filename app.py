from flask import Flask, render_template, request, redirect
import json
import datetime

app = Flask(__name__)


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



    