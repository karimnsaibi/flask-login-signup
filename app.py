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

# connect database
def get_db_connection():
    conn = sqlite3.connect('your_database.db')
    conn.row_factory = sqlite3.Row
    return conn

from routes.authentification import auth_bp
app.register_blueprint(auth_bp)

from routes.manage_sites import manage_site_bp
app.register_blueprint(manage_site_bp)

from routes.manage_site_codes import manage_site_codes_bp
app.register_blueprint(manage_site_codes_bp)


if __name__ == '__main__':
    app.run(debug=True)
