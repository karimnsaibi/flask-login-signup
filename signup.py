from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import re
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from email_utils import send_activation_email
from urllib.parse import quote
from datetime import datetime, timedelta
from auth_utils import generate_activation_token

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

app.secret_key = 'tunisie_telecom_dashboard'


# connect database
def get_db_connection():
    conn = sqlite3.connect('your_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/activate/<token>')  # Ensure this matches your generated link
def activate_account(token):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE activation_token = ?', 
        (token,)
    ).fetchone()

    if not user:
        conn.close()
        flash("Invalid activation link", "error")
        return redirect(url_for('login'))

    if datetime.now() > datetime.fromisoformat(user['token_expiry']):
        conn.close()
        flash("Activation link has expired", "error")
        return redirect(url_for('login'))

    # Activate account
    conn.execute('''
        UPDATE users 
        SET is_active = 1, activation_token = NULL 
        WHERE id = ?
    ''', (user['id'],))
    conn.commit()
    conn.close()

    flash("Account activated successfully!", "success")
    return redirect(url_for('login'))


# Sign up route
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        user_id = request.form['user_id']
        password = request.form['password']

        # 1. Validate email format and existence
        try:
            # This checks both format and DNS deliverability
            valid = validate_email(email, check_deliverability=True)
            email = valid.email  # Normalized email
        except EmailNotValidError as e:
            flash(f"Invalid email address: {str(e)}", "error")
            return redirect(url_for('signup'))

        # 2. Check if email/user_id already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE email = ? OR user_id = ?',
            (email, user_id)
        ).fetchone()
        
        if existing_user:
            conn.close()
            if existing_user['email'] == email:
                flash("Email already registered", "error")
            else:
                flash("User ID already taken", "error")
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        
        # Generate activation token
        activation_token = generate_activation_token()
        expiry = datetime.now() + timedelta(minutes=5)

        # Store user with activation data
        conn.execute('''
            INSERT INTO users (name, email, user_id, password, 
                            is_active, activation_token, token_expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, user_id, hashed_pw, False, activation_token, expiry))
        conn.commit()

        # Send activation email
        activation_link = f"{request.host_url}activate/{quote(activation_token)}"
        send_activation_email(email, activation_link)
        
        flash("Registration successful! Check your email to activate your account.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Log in route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  # Make sure you have this template

    # POST logic
    email = request.form['email']
    password = request.form['password']
    user_id = request.form['user_id']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? or user_id = ?', (email, user_id)).fetchone()
    conn.close()

    if user:
        if not user['is_active']:
            flash("Account not activated. Please check your email.", "error")
            return redirect(url_for('home'))
        elif check_password_hash(user['password'], password):
            return jsonify({
                'success': True,
                'message': 'Logged in successfully!',
                'category': 'success',
                'redirect': url_for('main')
            })
        else:
            flash("Invalid password.", "error")
            return redirect(url_for('home'))
    else:
        flash("User not found.", "error")
        return redirect(url_for('home'))
            


# Shell main page route
@app.route('/main')
def main():
    return "<h1>Welcome to the main page!</h1>"


# Helper function to print all users in the database
def print_all_users():
    conn = sqlite3.connect('your_database.db')  # Replace with your DB file name
    conn.row_factory = sqlite3.Row  # So we can access columns by name
    cursor = conn.cursor()

    rows = cursor.execute('SELECT * FROM users').fetchall()

    print("=== USERS TABLE ===")
    for row in rows:
        print(dict(row))  # Convert each row to a dictionary and print

    conn.close()

if __name__ == '__main__':
    print_all_users()  # Print all users when the app starts
    app.run(debug=True)