import secrets
from datetime import datetime, timedelta
from email_utils import send_email

def generate_activation_token():
    return secrets.token_urlsafe(32)  # 32-byte secure token

def is_token_valid(expiry_time):
    return datetime.now() < datetime.fromisoformat(expiry_time)

def send_activation_email(email, activation_link):
    subject = "Activate Your Account"
    body = f"""
    <html>
      <body>
        <p>Click this link to activate your account (expires in 5 minutes):</p>
        <a href="{activation_link}">{activation_link}</a>
        <p>If you didn't request this, please ignore this email.</p>
      </body>
    </html>
    """
    
    # Use your existing email sending function
    send_email(email, subject, body)