import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
import psutil
import time
import datetime
import threading
import secrets  # For generating secure tokens
from functools import wraps
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  # Generate a random secret key

# Database setup
DATABASE = 'users.db'

# Root folder for file overview
ROOT_FOLDER = os.path.join(app.root_path, 'files')


# Ensure the ROOT_FOLDER exists
if not os.path.exists(ROOT_FOLDER):
    try:
        os.makedirs(ROOT_FOLDER)
        print(f"Created ROOT_FOLDER: {ROOT_FOLDER}")
    except OSError as e:
        print(f"Error creating ROOT_FOLDER: {e}")



def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_server_data():
    """Collects server metrics."""
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        uptime = time.time() - psutil.boot_time()
        uptime_str = str(datetime.timedelta(seconds=int(uptime)))
        disk_io = psutil.disk_io_counters()

        global server_data
        if 'last_read_bytes' in server_data:
            read_bytes_diff = disk_io.read_bytes - server_data['last_read_bytes']
            read_speed_bytes = read_bytes_diff
            read_speed_mbps = read_speed_bytes / (1024 * 1024)
        else:
            read_speed_mbps = 0

        server_data['last_read_bytes'] = disk_io.read_bytes

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'uptime': uptime_str,
            'disk_read_speed': round(read_speed_mbps, 2),
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/files')
@login_required
def list_files():
    """Returns a list of files and directories in the specified folder."""
    path = request.args.get('path', '')  # Get the path from the query parameters
    target_path = os.path.join(ROOT_FOLDER, path)

    # Security check:  Prevent path traversal vulnerabilities
    target_path = os.path.abspath(target_path)  # Convert to absolute path
    if not target_path.startswith(os.path.abspath(ROOT_FOLDER)):
        return jsonify({'error': 'Path traversal attempt detected'}), 400  # Bad Request

    try:
        files = []
        for item_name in os.listdir(target_path):
            item_path = os.path.join(target_path, item_name)
            if os.path.isfile(item_path):
                item_type = 'file'
            elif os.path.isdir(item_path):
                item_type = 'directory'
            else:
                item_type = 'unknown'  # Handle symlinks or other special types

            files.append({'name': item_name, 'type': item_type})  # Include type


        return jsonify({'files': files})
    except FileNotFoundError:
        return jsonify({'error': 'Directory not found'}), 404
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        print(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Displays the main page (login if not logged in)."""
    if 'username' in session:
        return render_template('index.html', server_data=server_data, authenticated=True)
    else:
        return render_template('index.html', server_data=server_data, authenticated=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the password before storing it
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'}), 409  # Conflict
    else:
        return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    """Handles user login."""
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Hash the password to compare with the stored hash
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401  # Unauthorized


@app.route('/logout')
def logout():
    """Handles user logout."""
    session.pop('username', None)
    return redirect(url_for('index'), code=302) # Return 302 redirect


@app.route('/api/metrics')
@login_required
def get_metrics():
    global server_data
    data = get_server_data()
    if 'error' in data:
        print(f"Error in get_metrics: {data['error']}")
        return jsonify({'error': data['error']}), 500
    print(f"Sending JSON: {data}")
    return jsonify(data)


      
@app.route('/install')
@login_required
def install():
    """Serves the file for download."""
    filename = request.args.get('filename')
    path = request.args.get('path', '')  
    filepath = os.path.join(ROOT_FOLDER, path, filename)

    # Security check: Prevent path traversal
    filepath = os.path.abspath(filepath)
    if not filepath.startswith(os.path.abspath(ROOT_FOLDER)):
        return jsonify({'error': 'Path traversal attempt detected'}), 400

    try:
        return send_from_directory(
            os.path.dirname(filepath), 
            filename,                   
            as_attachment=True         
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

    


def update_server_data():
    global server_data
    while True:
        server_data = get_server_data()
        time.sleep(1)


if __name__ == '__main__':
    update_thread = threading.Thread(target=update_server_data)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, host='0.0.0.0')