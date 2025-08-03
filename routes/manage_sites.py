from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
from signup import get_db_connection, app

manage_site_bp = Blueprint('manage_site', __name__)


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
    governorates = ['Ariana','Béja','Ben Arous','Bizerte','Gabès','Gafsa',\
                    'Jendouba','Kairouan','Kasserine','Kebili','Kef','Mahdia',\
                    'Manouba','Médenine','Monastir','Nabeul','Sfax','Sidi Bouzid',\
                    'Siliana','Sousse','Tataouine','Tozeur','Tunis','Zaghouan']

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
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all code pools for the region
    cur.execute("SELECT start_code, end_code FROM site_code_pools WHERE region = ?", (region,))
    rows = cur.fetchall()

    # Expand ranges into a list of codes
    codes = []
    for row in rows:
        start = int(row['start_code'])
        end = int(row['end_code'])
        codes.extend(list(range(start, end + 1)))

    conn.close()

    # Only return codes. Delegations are handled in frontend.
    return jsonify({"codes": codes})
