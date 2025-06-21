from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Mail instance
mail = Mail()

def send_email(to, otp, name):
    """
    Send an email with the OTP code to the specified email address.
    
    Args:
        to (str): Recipient email address
        otp (str): One-time password code
        name (str): Recipient's name
    """    
    subject = "Your OTP Code"
    body = f"Hi {name},\nYour OTP code is: {otp}"
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            sender=(os.getenv('MAIL_DEFAULT_SENDER_NAME', 'DORMEASE'), 
                   os.getenv('MAIL_DEFAULT_SENDER_EMAIL', 'smtp.testpersonal2004@gmail.com'))
        )
        mail.send(msg)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

def send_notification_email(to, subject, body):
    """
    Send a notification email with custom subject and body.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Email body content
    """    
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            sender=(os.getenv('MAIL_DEFAULT_SENDER_NAME', 'DORMEASE'), 
                   os.getenv('MAIL_DEFAULT_SENDER_EMAIL', 'smtp.testpersonal2004@gmail.com'))
        )
        mail.send(msg)
        return True
    except Exception as e:
        print("Error sending notification email:", e)
        return False

def configure_mail(app):
    """
    Configure Flask-Mail with application settings using environment variables.
    
    Args:
        app: Flask application instance
    """
    # Flask-Mail configuration using environment variables
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = (
        os.getenv('MAIL_DEFAULT_SENDER_NAME', 'DORMEASE'),
        os.getenv('MAIL_DEFAULT_SENDER_EMAIL', 'smtp.testpersonal2004@gmail.com')
    )
    
    # Validate that required environment variables are set
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        raise ValueError("MAIL_USERNAME and MAIL_PASSWORD must be set in environment variables")
    
    # Initialize mail with the app
    mail.init_app(app)
