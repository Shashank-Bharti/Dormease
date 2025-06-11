from flask import redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email
from functools import wraps
import random
from models import User, otp_store
from email_service import send_email

# Forms for authentication
class RegisterForm(FlaskForm):
    """Form for user registration."""
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Get OTP')

class OTPForm(FlaskForm):
    """Form for OTP verification."""
    email = HiddenField('Email', validators=[DataRequired(), Email()])
    otp = StringField('OTP', validators=[DataRequired()])
    submit = SubmitField('Submit OTP')

class LoginForm(FlaskForm):
    """Form for user login."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Get OTP')

# Login required decorator
def login_required(f):
    """
    Decorator to ensure user is logged in before accessing a route.
    Redirects to login page if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        # Make sure the user still exists in the database
        user = User.query.filter_by(email=session['user_email']).first()
        if not user:
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_otp():
    """Generate a random 5-digit OTP."""
    return str(random.randint(10000, 99999))

def send_login_otp(email):
    """
    Generate and send OTP for login.
    
    Args:
        email (str): User's email address
        
    Returns:
        bool: True if OTP sent successfully, False otherwise
    """
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    
    otp = generate_otp()
    otp_store[email] = {'otp': otp}
    return send_email(email, otp, user.name)

def send_registration_otp(email, name, surname):
    """
    Generate and send OTP for registration.
    
    Args:
        email (str): User's email address
        name (str): User's first name
        surname (str): User's last name
        
    Returns:
        str: Generated OTP if successful, None otherwise
    """
    otp = generate_otp()
    otp_store[email] = {'otp': otp, 'name': name, 'surname': surname}
    if send_email(email, otp, name):
        return otp
    return None

def verify_otp(email, otp_input):
    """
    Verify the OTP provided by the user.
    
    Args:
        email (str): User's email address
        otp_input (str): OTP provided by the user
        
    Returns:
        bool: True if OTP is valid, False otherwise
    """
    if email in otp_store and otp_store[email]['otp'] == otp_input:
        return True
    return False
