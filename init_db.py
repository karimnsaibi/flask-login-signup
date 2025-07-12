import sqlite3
import os

def init_db():
    # Delete old database if exists
    if os.path.exists('your_database.db'):
        os.remove('your_database.db')
    
    conn = sqlite3.connect('your_database.db')
    cur = conn.cursor()
    
    # Add these columns to your users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        user_id TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 0,
        activation_token TEXT,
        token_expiry DATETIME,
        twofa_code TEXT,
        twofa_expiry TEXT,
        last_2fa_sent TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database created with updated schema")

if __name__ == '__main__':
    init_db()