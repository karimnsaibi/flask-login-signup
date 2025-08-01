from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import re
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from email_utils import send_activation_email, send_email
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
        # email = request.form['email']
        user_id = request.form['user_id']
        password = request.form['password']
        password2 = request.form['password2']
        profile = request.form['profile']  

        # 1. Validate email format and existence
        # try:
        #     # This checks both format and DNS deliverability
        #     valid = validate_email(email, check_deliverability=True)
        #     email = valid.email  # Normalized email
        # except EmailNotValidError as e:
        #     flash(f"Invalid email address: {str(e)}", "error")
        #     return redirect(url_for('signup'))

        # 2. Check if email/user_id already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            # 'SELECT * FROM users WHERE email = ? OR user_id = ?',
            # (email, user_id)
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        if existing_user:
            # conn.close()
            # if existing_user['email'] == email:
            #     flash("Email already registered", "error")
            # else:
            #     flash("User ID already taken", "error")
            flash("User ID already taken", "error")
            conn.close()
            return redirect(url_for('signup'))
        if password != password2:
            flash("Passwords do not match", "error")
            conn.close()
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        
        # # Generate activation token
        # activation_token = generate_activation_token()
        # expiry = datetime.now() + timedelta(minutes=5)

        # Store user with activation data
        # conn.execute('''
        #     INSERT INTO users (name, email, user_id, profile, password, 
        #                     is_active, activation_token, token_expiry)
        #     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        # ''', (name, email, user_id, profile, hashed_pw, False, activation_token, expiry))
        # conn.commit()

        # # Send activation email
        # activation_link = f"{request.host_url}activate/{quote(activation_token)}"
        # send_activation_email(email, activation_link)
        
        # flash("Registration successful! Check your email to activate your account.", "success")
        
        # Store user with activation data
        conn.execute('''
         INSERT INTO users (name, user_id, profile, password)
         VALUES (?, ?, ?, ?)
        ''', (name, user_id, profile, hashed_pw))
        conn.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Log in route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST logic
    # email = request.form['email']
    password = request.form['password']
    user_id = request.form['user_id']

    conn = get_db_connection()
    # user = conn.execute('SELECT * FROM users WHERE email = ? or user_id = ?', (email, user_id)).fetchone()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()

    if user:
        # if not user['is_active']:
        #     flash("Account not activated. Please check your email.", "error")
        #     return redirect(url_for('home'))
        if check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['profile'] = user['profile']
            return redirect(url_for('main'))
            # # Generate 6-digit code
            # import random
            # code = f"{random.randint(100000, 999999)}"
            # expiry = datetime.now() + timedelta(minutes=5)

            # # Save code and expiry
            # conn = get_db_connection()
            # conn.execute(
            #     'UPDATE users SET twofa_code = ?, twofa_expiry = ? WHERE id = ?',
            #     (code, expiry.isoformat(), user['id'])
            # )
            # conn.commit()
            # conn.close()

            # # Send 2FA code via email
            # send_email(user['email'], "Your 2FA Code", f"<p>Your 2FA verification code is: <strong>{code}</strong></p>")

            # # Store user ID in session
            # session['2fa_user_id'] = user['id']
            # return redirect(url_for('two_fa'))
        flash("Invalid password", "error")
        return redirect(url_for('home'))
    flash("Invalid user ID", "error")
    return redirect(url_for('home'))


# Two Factor Authentication route
@app.route('/2fa', methods=['GET', 'POST'])
def two_fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        entered_code = request.form['code']
        user_id = session['2fa_user_id']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if user:
            if (user['twofa_code'] == entered_code and 
                datetime.now() < datetime.fromisoformat(user['twofa_expiry'])):
                # Clear 2FA and grant access
                conn.execute('''
                    UPDATE users SET twofa_code = NULL, twofa_expiry = NULL WHERE id = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                session.pop('2fa_user_id')
                session['user_id'] = user_id  # Mark user as logged in
                return redirect(url_for('main'))
            else:
                flash("Invalid or expired code", "error")
        conn.close()

    return render_template('2fa.html')





# Shell main page route
@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('main.html')


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

# Resend 2FA code route
@app.route('/resend-2fa')
def resend_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['2fa_user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for('home'))

    # Rate limiting: block resending if last_2fa_sent was less than 30 seconds ago
    now = datetime.now()
    if user['last_2fa_sent']:
        last_sent = datetime.fromisoformat(user['last_2fa_sent'])
        if now < last_sent + timedelta(seconds=30):
            conn.close()
            flash("Please wait before requesting a new code.", "warning")
            return redirect(url_for('two_fa'))

    # If the previous code is still valid, reuse it
    if user['twofa_expiry'] and datetime.now() < datetime.fromisoformat(user['twofa_expiry']):
        code = user['twofa_code']
    else:
        # Generate new 6-digit code
        import random
        code = f"{random.randint(100000, 999999)}"
        expiry = now + timedelta(minutes=5)

        conn.execute('''
            UPDATE users SET twofa_code = ?, twofa_expiry = ? WHERE id = ?
        ''', (code, expiry.isoformat(), user_id))
        conn.commit()

    # Send the email
    send_email(user['email'], "Your 2FA Code", f"<p>Your verification code is: <strong>{code}</strong></p>")

    # Update last_2fa_sent
    conn.execute('UPDATE users SET last_2fa_sent = ? WHERE id = ?', (now.isoformat(), user_id))
    conn.commit()
    conn.close()

    flash("A new verification code has been sent to your email.", "success")
    return redirect(url_for('two_fa'))

# Helper Functions
def site_exists(conn, region, delegation, code):
    return conn.execute('SELECT 1 FROM site WHERE region=? AND delegation=? AND code=?', 
                        (region, delegation, code)).fetchone()

def add_site(conn, data):
    if site_exists(conn, data['region'], data['delegation'], data['site_code']):
        return False, 'Site already exists'

    conn.execute('''
        INSERT INTO site VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['region'], data['site_code'], data['delegation'], data['site_name'],
        data['x'], data['y'], data['hba'], data['supplier'], 
        data['access'], data['antenna'], data['surface']
    ))
    conn.commit()
    return True, 'Site added successfully'

def delete_site(conn, region, delegation, code):
    if not site_exists(conn, region, delegation, code):
        return False, 'Site not found'
    conn.execute('DELETE FROM site WHERE region=? AND delegation=? AND code=?', 
                 (region, delegation, code))
    conn.commit()
    return True, 'Site deleted successfully'

def edit_site(conn, data):
    if not site_exists(conn, data['region'], data['delegation'], data['site_code']):
        return False, 'Site not found'
    conn.execute('''
        UPDATE site SET site_name=?, x=?, y=?, hba=?, supplier=?, access=?, antenna=?, surface=?
        WHERE region=? AND delegation=? AND code=?
    ''', (
        data['site_name'], data['x'], data['y'], data['hba'],
        data['supplier'], data['access'], data['antenna'], data['surface'],
        data['region'], data['delegation'], data['site_code']
    ))
    conn.commit()
    return True, 'Site updated successfully'

# Main route
@app.route('/manage-sites', methods=['GET', 'POST'])
def manage_site():
    conn = get_db_connection()
    governorates = [row['region'] for row in conn.execute('SELECT DISTINCT region FROM site_code_pools')]

    if request.method == 'POST':
        data = request.form.to_dict()
        action = data['action']

        if action == 'add':
            success, message = add_site(conn, data)
        elif action == 'edit':
            success, message = edit_site(conn, data)
        elif action == 'delete':
            success, message = delete_site(conn, data['region'], data['delegation'], data['site_code'])
        else:
            success, message = False, 'Invalid action'

        flash(message, 'success' if success else 'error')
        conn.close()
        return redirect(url_for('manage_site'))

    conn.close()
    return render_template('manage_sites.html', governorates=governorates)




@app.route('/api/site-info')
def site_info():
    region = request.args.get('region')
    rows = get_db_connection().execute('SELECT start_code,end_code,delegation FROM site_code_pools WHERE region=?', (region,)).fetchall()
    codes = sorted([str(c) for r in rows for c in range(r['start_code'], r['end_code']+1)])
    delegations = sorted({r['delegation'] for r in rows})
    return jsonify(codes=codes, delegations=delegations)

















    """Additional features: Support SMS 2FA later (using Twilio or similar)"""


from flask import jsonify, request

def code_pool_exists(conn, region, start_code, end_code):
    return conn.execute(
        'SELECT 1 FROM site_code_pools WHERE region=? AND start_code=? AND end_code=?',
        (region, start_code, end_code)
    ).fetchone()

def add_code_pool(conn, region, start_code, end_code):
    if code_pool_exists(conn, region, start_code, end_code):
        return False, "Code pool already exists for this region."
    conn.execute(
        'INSERT INTO site_code_pools (region, start_code, end_code) VALUES (?, ?, ?)',
        (region, start_code, end_code)
    )
    conn.commit()
    return True, "Code pool added successfully."

def get_code_pools(conn, region):
    rows = conn.execute(
        'SELECT start_code, end_code FROM site_code_pools WHERE region=? ORDER BY start_code',
        (region,)
    ).fetchall()
    return [{'start_code': row['start_code'], 'end_code': row['end_code']} for row in rows]

def delete_code_pools(conn, region, pools):
    for pool in pools:
        conn.execute(
            'DELETE FROM site_code_pools WHERE region=? AND start_code=? AND end_code=?',
            (region, pool['start_code'], pool['end_code'])
        )
    conn.commit()
    return True, "Selected code pools deleted."

def edit_code_pools(conn, region, updates):
    for update in updates:
        # We identify the old pool by old_start and update to new start_code and end_code
        old_start = update.get('old_start')
        old_end = update.get('old_end')
        new_start = update.get('start_code')
        new_end = update.get('end_code')
        if old_start is None or old_end is None:
            continue
        conn.execute(
            'UPDATE site_code_pools SET start_code=?, end_code=? WHERE region=? AND start_code=? AND end_code=?',
            (new_start, new_end, region, old_start, old_end)
        )
    conn.commit()
    return True, "Selected code pools updated."

@app.route('/manage-site-codes')
def manage_site_codes():
    return render_template('manage_site_codes.html')

@app.route('/manage-site-codes/add', methods=['POST'])
def add_site_code_pool():
    data = request.get_json()
    region = data.get('region')
    start_code = data.get('start_code')
    end_code = data.get('end_code')
    if not region or start_code is None or end_code is None or start_code >= end_code:
        return jsonify(success=False, message="Invalid input data."), 400
    conn = get_db_connection()
    success, message = add_code_pool(conn, region, start_code, end_code)
    conn.close()
    return jsonify(success=success, message=message)

@app.route('/manage-site-codes/exploit')
def exploit_site_code_pools():
    region = request.args.get('region')
    if not region:
        return jsonify(success=False, message="Region parameter is required."), 400
    conn = get_db_connection()
    code_pools = get_code_pools(conn, region)
    conn.close()
    return jsonify(success=True, code_pools=code_pools)

@app.route('/manage-site-codes/delete', methods=['POST'])
def delete_site_code_pools():
    data = request.get_json()
    region = data.get('region')
    pools = data.get('pools', [])
    if not region or not pools:
        flash("Invalid input data.", "error")
        return redirect(url_for('manage_site_codes'))
    conn = get_db_connection()
    success, message = delete_code_pools(conn, region, pools)
    conn.close()
    flash(message, "success" if success else "error")
    return redirect(url_for('manage_site_codes'))

@app.route('/manage-site-codes/edit', methods=['POST'])
def edit_site_code_pools():
    data = request.get_json()
    region = data.get('region')
    updates = data.get('updates', [])
    if not region or not updates:
        flash("Invalid input data.", "error")
        return redirect(url_for('manage_site_codes'))
    conn = get_db_connection()
    # Each update should have old_start, old_end, start_code, end_code
    # But frontend currently sends old_start only as index, so we need to adjust frontend or handle here
    # For now, assume frontend sends old_start and old_end properly
    success, message = edit_code_pools(conn, region, updates)
    conn.close()
    flash(message if success else "Error updating selected rows", "success" if success else "error")
    return redirect(url_for('manage_site_codes'))

if __name__ == '__main__':
    app.run(debug=True)
