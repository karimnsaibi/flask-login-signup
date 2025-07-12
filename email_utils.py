import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os

# Email configuration (use environment variables in production)
SMTP_SERVER = "smtp.gmail.com"  # For Gmail (or your SMTP provider)
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER", "mohamedkarimnsaibi@gmail.com")  # Use environment variables
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD", "okta ahws cgti vlib")  # App password for Gmail

def send_email(to_email, subject, body_html):
    """Send an HTML email with the given content"""
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email

        # Attach HTML body
        msg.attach(MIMEText(body_html, 'html'))

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_activation_email(email, activation_link):
    """Specialized function for sending activation emails"""
    subject = "Activate Your Account"
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Account Activation</h2>
            <p>Please click the link below to activate your account (expires in 5 minutes):</p>
            <p><a href="{activation_link}" style="
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
                display: inline-block;
            ">Activate Account</a></p>
            <p>Or copy this link to your browser:<br>
            <code>{activation_link}</code></p>
            <hr>
            <p style="color: #666; font-size: 0.9em;">
                If you didn't request this, please ignore this email.
            </p>
        </body>
    </html>
    """
    return send_email(email, subject, html_content)