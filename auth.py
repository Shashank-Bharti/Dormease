from flask import redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email
from functools import wraps
import random
from datetime import datetime, timedelta
from models import User, OTP, otp_store, db
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

def cleanup_expired_otps():
    """Remove expired OTPs from database."""
    try:
        expired_otps = OTP.query.filter(OTP.expires_at < datetime.now()).all()
        for otp in expired_otps:
            db.session.delete(otp)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up expired OTPs: {e}")

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
    
    try:
        # Clean up any existing OTPs for this email
        existing_otps = OTP.query.filter_by(email=email, otp_type='login').all()
        for otp in existing_otps:
            db.session.delete(otp)
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        
        # Store OTP in database
        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            otp_type='login',
            expires_at=expires_at
        )
        db.session.add(new_otp)
        db.session.commit()
        
        # Send email
        return send_email(email, otp_code, user.name)
    
    except Exception as e:
        db.session.rollback()
        print(f"Error sending login OTP: {e}")
        return False

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
    try:
        # Clean up any existing OTPs for this email
        existing_otps = OTP.query.filter_by(email=email, otp_type='registration').all()
        for otp in existing_otps:
            db.session.delete(otp)
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        
        # Store OTP in database
        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            name=name,
            surname=surname,
            otp_type='registration',
            expires_at=expires_at
        )
        db.session.add(new_otp)
        db.session.commit()
        
        # Send email
        if send_email(email, otp_code, name):
            return otp_code
        return None
    
    except Exception as e:
        db.session.rollback()
        print(f"Error sending registration OTP: {e}")
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
    try:
        # Clean up expired OTPs first
        cleanup_expired_otps()
        
        # Find the most recent valid OTP for this email
        otp_record = OTP.query.filter_by(
            email=email, 
            otp_code=otp_input,
            is_used=False
        ).filter(OTP.expires_at > datetime.now()).first()
        
        if otp_record:
            # Mark OTP as used
            otp_record.is_used = True
            db.session.commit()
            return True
        return False
    
    except Exception as e:
        db.session.rollback()
        print(f"Error verifying OTP: {e}")
        return False

def get_otp_data(email, otp_input):
    """
    Get OTP data for registration (name, surname).
    
    Args:
        email (str): User's email address
        otp_input (str): OTP provided by the user
        
    Returns:
        dict: OTP data with name and surname, or None if not found
    """
    try:
        otp_record = OTP.query.filter_by(
            email=email, 
            otp_code=otp_input,
            otp_type='registration',
            is_used=True  # Should be marked as used after verification
        ).first()
        
        if otp_record:
            return {
                'name': otp_record.name,
                'surname': otp_record.surname
            }
        return None
    
    except Exception as e:
        print(f"Error getting OTP data: {e}")
        return None
