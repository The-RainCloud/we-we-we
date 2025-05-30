import sqlite3
import hashlib
import secrets
import string

DATABASE = 'users.db'  # Same database as the main app

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table(): # Create the users table.
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

def generate_password(length=12):
    """Generates a strong random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def add_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"User {username} added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: Username {username} already exists.")
    finally:
        conn.close()

if __name__ == "__main__":
    create_table()
    while True:
        username = input("Enter username: ")
        if not username:
            break  # Exit if username is empty

        auto_generate = input("Generate password automatically? (y/n): ").lower()
        if auto_generate == 'y':
            password = generate_password()
            print(f"Generated password: {password}") # Display password. IMPORTANT: Consider how to securely transfer this.
        else:
            password = input("Enter password: ")

        add_user(username, password)