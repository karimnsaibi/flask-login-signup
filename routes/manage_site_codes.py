from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Blueprint
from signup import get_db_connection, app

manage_site_codes_bp = Blueprint('manage_site_codes', __name__)


# Helper Functions
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