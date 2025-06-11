from flask_mail import Mail, Message

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
            sender=("DORMEASE", "your_email") 
        )
        mail.send(msg)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

def configure_mail(app):
    """
    Configure Flask-Mail with application settings.
    
    Args:
        app: Flask application instance
    """
    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your_email'
    app.config['MAIL_PASSWORD'] = 'your_password_here'  
    app.config['MAIL_DEFAULT_SENDER'] = ('DORMEASE','your_email')
    
    # Initialize mail with the app
    mail.init_app(app)
