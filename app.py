# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import CSRFProtect

from models import db, User, otp_store
from email_service import configure_mail, send_email
from auth import RegisterForm, OTPForm, LoginForm, login_required, send_login_otp, send_registration_otp, verify_otp
from utils import add_no_cache_headers

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure session security
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restrict cookie sending to same-site requests
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # Session expires after 30 minutes

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure CSRF protection
csrf = CSRFProtect(app)

# Configure email service
configure_mail(app)

@app.before_request
def create_tables():
    """Create database tables if they don't exist."""
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True
        
# All routes are defined here
@app.route('/')
def home():
    """Render the home page."""
    response = render_template('home.html')
    response = add_no_cache_headers(response)
    return response

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/registration', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    form = RegisterForm()  # For CSRF protection
    otp_form = OTPForm()   # For OTP handling
    
    if request.method == 'POST':
        # Get data from HTML form inputs
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        
        # Manual validation
        if not name or not surname or not email:
            flash('All fields are required')
            return render_template('registration.html', form=form, otp_form=otp_form)
        else:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered. Please login instead.')
                return redirect(url_for('login'))
            
            # Generate OTP if user doesn't exist
            otp = send_registration_otp(email, name, surname)
            if otp:
                flash('OTP sent to your email.')
                otp_form.email.data = email
                
                # Form data (name, surname, email) will be preserved through request.form.get in the template
                return render_template('registration.html', form=form, otp_form=otp_form)
            else:
                flash('Failed to send OTP. Please try again.')
                return render_template('registration.html', form=form, otp_form=otp_form)
        
    return render_template('registration.html', form=form, otp_form=otp_form)

@app.route('/verify_signup', methods=['POST'])
def verify_signup():
    """Verify OTP and complete user registration."""
    otp_form = OTPForm()
    if otp_form.validate_on_submit():
        email = otp_form.email.data
        otp_input = otp_form.otp.data
        
        if verify_otp(email, otp_input):
            name = otp_store[email]['name']
            surname = otp_store[email]['surname']
            
            # Create new user if not exists
            if not User.query.filter_by(email=email).first():
                new_user = User(name=name, surname=surname, email=email)
                db.session.add(new_user)
                db.session.commit()
            
            # Clear OTP from store
            otp_store.pop(email)
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('register'))
    else:
        flash('Something went wrong. Please try again.')
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    form = LoginForm()  # For CSRF protection
    otp_form = OTPForm()  # For OTP handling
    
    if request.method == 'POST':
        # Get data from HTML form input
        email = request.form.get('email')
        
        # Manual validation
        if not email:
            flash('Email is required')
            return render_template('login.html', form=form, otp_form=otp_form)
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                if send_login_otp(email):
                    flash('Login OTP sent to your email.')
                    otp_form.email.data = email
                    # The email value will be preserved through request.form.get in the template
                    return render_template('login.html', form=form, otp_form=otp_form)
                else:
                    flash('Failed to send OTP. Please try again.')
                    return render_template('login.html', form=form, otp_form=otp_form)
            else:
                flash('User not found. Please register first.')
                return redirect(url_for('register'))
    
    return render_template('login.html', form=form, otp_form=otp_form)

@app.route('/verify_login', methods=['POST'])
def verify_login():
    """Verify OTP and log in user."""
    otp_form = OTPForm()
    if otp_form.validate_on_submit():
        email = otp_form.email.data
        otp_input = otp_form.otp.data
        
        if verify_otp(email, otp_input):
            session['user_email'] = email
            otp_store.pop(email)
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('login'))
    else:
        flash('Something went wrong. Please try again.')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard for logged-in users."""
    user = User.query.filter_by(email=session['user_email']).first()
    response = render_template('dashboard.html', user=user)
    return add_no_cache_headers(response)

@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    session.clear()
    flash('Logged out successfully.')
    response = redirect(url_for('home'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/verification')
@login_required
def verification():
    """Render the verification page."""
    user = User.query.filter_by(email=session['user_email']).first()
    response = render_template('verify.html', user=user)
    return add_no_cache_headers(response)

@app.route('/recipients')
@login_required
def recipients():
    """Render the recipients page."""
    user = User.query.filter_by(email=session['user_email']).first()
    response = render_template('recipients.html', user=user)
    return add_no_cache_headers(response)

@app.route('/datasets')
@login_required
def datasets():
    """Render the datasets page."""
    user = User.query.filter_by(email=session['user_email']).first()
    response = render_template('datasets.html', user=user)
    return add_no_cache_headers(response)

@app.route('/issues')
@login_required
def issues():
    """Render the issues page."""
    user = User.query.filter_by(email=session['user_email']).first()
    response = render_template('notfound.html', user=user)
    return add_no_cache_headers(response)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("notfound.html"), 404

if __name__ == '__main__':
    app.run(debug=True, port=3000)
