# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_wtf import CSRFProtect
import pandas as pd
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

from models import db, User, Dataset, Recipient, OTP, otp_store
from email_service import configure_mail, send_email
from auth import RegisterForm, OTPForm, LoginForm, login_required, send_login_otp, send_registration_otp, verify_otp
from utils import add_no_cache_headers

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key_here_change_in_production')

# Configure Flask debug mode from environment
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Configure session security

app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Restrict cookie sending to same-site requests
app.config['PERMANENT_SESSION_LIFETIME'] = 84600  # Session expires after 30 minutes

# Configure database

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Configure CSRF (cross site request forgery) - wtforms protection
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
            # Get OTP data (name, surname) from database
            from auth import get_otp_data
            otp_data = get_otp_data(email, otp_input)
            
            if otp_data:
                name = otp_data['name']
                surname = otp_data['surname']
                
                # Create new user if not exists
                if not User.query.filter_by(email=email).first():
                    new_user = User(name=name, surname=surname, email=email)
                    db.session.add(new_user)
                    db.session.commit()
                
                flash('Account created successfully! Please log in.')
                return redirect(url_for('login'))
            else:
                flash('OTP data not found. Please try registration again.')
                return redirect(url_for('register'))
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
            flash('Login successful!')
            return redirect(url_for('datasets'))
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('login'))
    else:
        flash('Something went wrong. Please try again.')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():

    """Render the analytics dashboard page."""
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
    """Render the verification page with QR scanner."""
    user = User.query.filter_by(email=session['user_email']).first()
    # Get user's datasets for the dropdown
    datasets = user.datasets
    response = render_template('verify.html', user=user, datasets=datasets)
    return add_no_cache_headers(response)

@app.route('/recipients')
@login_required
def recipients():


    """Render the test recipients page."""
    user = User.query.filter_by(email=session['user_email']).first()
    
    # Get dataset filter from query params
    dataset_id = request.args.get('dataset_id', type=int)
    
    # Get all datasets for the user for the filter dropdown
    user_datasets = Dataset.query.filter_by(user_id=user.id).order_by(Dataset.uploaded_at.desc()).all()
    
    # Get recipients based on filter
    if dataset_id:
        recipients = Recipient.query.filter_by(dataset_id=dataset_id).order_by(Recipient.room_no, Recipient.name).all()
        selected_dataset = Dataset.query.get(dataset_id)
    else:
        # Get all recipients for the user
        dataset_ids = [d.id for d in user_datasets]
        recipients = Recipient.query.filter(Recipient.dataset_id.in_(dataset_ids)).order_by(Recipient.room_no, Recipient.name).all()
        selected_dataset = None
    
    response = render_template('recipients.html', user=user, recipients=recipients, 
                             datasets=user_datasets, selected_dataset=selected_dataset)
    return add_no_cache_headers(response)

@app.route('/datasets')
@login_required
def datasets():
    """Render the datasets page."""
    user = User.query.filter_by(email=session['user_email']).first()
    user_datasets = Dataset.query.filter_by(user_id=user.id).order_by(Dataset.uploaded_at.desc()).all()
    response = render_template('datasets.html', user=user, datasets=user_datasets)
    return add_no_cache_headers(response)

# @app.route('/test-datasets')
# @login_required
# def test_datasets():
#     """Render the test datasets page."""
#     user = User.query.filter_by(email=session['user_email']).first()
#     user_datasets = Dataset.query.filter_by(user_id=user.id).order_by(Dataset.uploaded_at.desc()).all()
#     response = render_template('test-datasets.html', user=user, datasets=user_datasets)
#     return add_no_cache_headers(response)

@app.route('/upload_dataset', methods=['POST'])
@login_required
def upload_dataset():
    """Handle CSV upload and process room allocation."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        
        # Get form data
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(url_for('datasets'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('datasets'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file')
            return redirect(url_for('datasets'))
        
        # Get other form data
        gender = request.form.get('gender')
        floors = int(request.form.get('floors'))
        rooms_per_floor = int(request.form.get('rooms'))
        occupancy_per_room = int(request.form.get('occupancy'))
        hostel_name = request.form.get('hostel-name')
        extra_info = request.form.get('extra-info', '')
        
        # Calculate total capacity
        total_capacity = (floors + 1) * rooms_per_floor * occupancy_per_room
        
        # Read and process CSV
        df = pd.read_csv(file)
        
        # Check if required columns exist
        required_columns = ['name', 'gender']
        missing_columns = [col for col in required_columns if col.lower() not in [c.lower() for c in df.columns]]
        if missing_columns:
            flash(f'CSV must contain columns: {", ".join(missing_columns)}')
            return redirect(url_for('datasets'))
        
        # Normalize column names to lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # Filter by gender
        df_filtered = df[df['gender'].str.lower() == gender.lower()].copy()
        
        if df_filtered.empty:
            flash(f'No {gender} recipients found in the CSV')
            return redirect(url_for('datasets'))
        
        # Sort by name A-Z
        df_filtered = df_filtered.sort_values('name')
        
        # Check if we have enough capacity
        if len(df_filtered) > total_capacity:
            flash(f'Not enough capacity! You have {len(df_filtered)} recipients but only {total_capacity} slots. Please increase occupancy or rooms.')
            return redirect(url_for('datasets'))
        
        # Create dataset record
        dataset = Dataset(
            name=f"{hostel_name}_{gender}_{len(df_filtered)}_recipients",
            hostel_name=hostel_name,
            gender=gender,
            floors=floors,
            rooms_per_floor=rooms_per_floor,
            occupancy_per_room=occupancy_per_room,
            extra_info=extra_info,
            total_capacity=total_capacity,
            user_id=user.id
        )
        db.session.add(dataset)
        db.session.flush()  # Get the dataset ID
        
        # Allocate rooms
        recipient_index = 0
        for floor in range(floors + 1):  # 0 to floors
            for room in range(1, rooms_per_floor + 1):
                room_no = f"{floor:01d}{room:02d}"  # Format: 001, 002, 101, 102, etc.
                
                for bed in range(occupancy_per_room):
                    if recipient_index >= len(df_filtered):
                        break
                    
                    recipient_data = df_filtered.iloc[recipient_index]
                    
                    # Get email and phone safely, handling NaN values
                    email = str(recipient_data['email']) if 'email' in df_filtered.columns and pd.notna(recipient_data['email']) else ''
                    
                    # Check for phone or mobile column - handle both naming conventions
                    if 'phone' in df_filtered.columns and pd.notna(recipient_data['phone']):
                        phone = str(recipient_data['phone'])
                    elif 'mobile' in df_filtered.columns and pd.notna(recipient_data['mobile']):
                        phone = str(recipient_data['mobile'])
                    else:
                        phone = ''
                    
                    # Create recipient record
                    recipient = Recipient(
                        name=recipient_data['name'],
                        gender=recipient_data['gender'],
                        room_no=room_no,
                        hostel_allotted=hostel_name,
                        email=email,
                        phone=phone,
                        dataset_id=dataset.id
                    )
                    db.session.add(recipient)
                    recipient_index += 1
                
                if recipient_index >= len(df_filtered):
                    break
            
            if recipient_index >= len(df_filtered):
                break
        
        db.session.commit()
        flash(f'Successfully allocated {len(df_filtered)} recipients to {hostel_name}!')
        return redirect(url_for('datasets'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('datasets'))

@app.route('/recipients-test')
@login_required
def recipients_test():
    """Render the test recipients page."""
    user = User.query.filter_by(email=session['user_email']).first()
    
    # Get dataset filter from query params
    dataset_id = request.args.get('dataset_id', type=int)
    
    # Get all datasets for the user for the filter dropdown
    user_datasets = Dataset.query.filter_by(user_id=user.id).order_by(Dataset.uploaded_at.desc()).all()
    
    # Get recipients based on filter
    if dataset_id:
        recipients = Recipient.query.filter_by(dataset_id=dataset_id).order_by(Recipient.room_no, Recipient.name).all()
        selected_dataset = Dataset.query.get(dataset_id)
    else:
        # Get all recipients for the user
        dataset_ids = [d.id for d in user_datasets]
        recipients = Recipient.query.filter(Recipient.dataset_id.in_(dataset_ids)).order_by(Recipient.room_no, Recipient.name).all()
        selected_dataset = None
    
    response = render_template('test-recipients.html', user=user, recipients=recipients, 
                             datasets=user_datasets, selected_dataset=selected_dataset)
    return add_no_cache_headers(response)

@app.route('/toggle_checkin/<int:recipient_id>', methods=['POST'])
@login_required
def toggle_checkin(recipient_id):
    """Toggle check-in status for a recipient."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        recipient = Recipient.query.get_or_404(recipient_id)
        
        # Verify the recipient belongs to user's dataset
        if recipient.dataset.user_id != user.id:
            flash('Unauthorized access')
            return redirect(url_for('recipients'))
        
        # Toggle status
        if recipient.status == 'Checked In':
            recipient.status = 'Not Checked In'
            flash(f'{recipient.name} checked out successfully!')
        else:
            recipient.status = 'Checked In'
            flash(f'{recipient.name} checked in successfully!')
        
        db.session.commit()
        return redirect(url_for('recipients'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}')
        return redirect(url_for('recipients'))

# @app.route('/test-verification')
# @login_required
# def test_verification():
#     """Render the test verification page with QR scanner."""
#     user = User.query.filter_by(email=session['user_email']).first()
#     # Get user's datasets for the dropdown
#     datasets = user.datasets
#     response = render_template('test-verification.html', user=user, datasets=datasets)
#     return add_no_cache_headers(response)

@app.route('/verify_qr_scan', methods=['POST'])
@login_required
def verify_qr_scan():
    """Handle QR scan verification and update recipient status."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        data = request.get_json()
        
        name = data.get('name', '').strip()
        roll_no = data.get('roll_no', '').strip()
        mobile = data.get('mobile', '').strip()
        scan_mode = data.get('scan_mode')  # 'checkin' or 'checkout'
        dataset_id = data.get('dataset_id')  # Specific dataset to search in
        
        print(f"DEBUG: QR Scan - Name: '{name}', Mobile: '{mobile}', Scan Mode: '{scan_mode}', Dataset ID: '{dataset_id}'")
        
        if not name or not scan_mode:
            return jsonify({
                'success': False,
                'message': 'Invalid QR data: Name and scan mode are required.'
            })
        
        if not dataset_id:
            return jsonify({
                'success': False,
                'message': 'Dataset ID is required. Please select a dataset before scanning.'
            })
        
        # Verify that the dataset belongs to the user
        dataset = Dataset.query.filter_by(id=dataset_id, user_id=user.id).first()
        if not dataset:
            return jsonify({
                'success': False,
                'message': 'Invalid dataset or access denied.'
            })
        
        print(f"DEBUG: Using dataset: {dataset.hostel_name} - {dataset.gender}")
        
        # Find matching recipient in the specific dataset only
        recipient = None
        match_method = "unknown"  # Track how the recipient was found
         # Find matching recipient in the specific dataset only
        recipient = None
        
        # Primary match: exact name and mobile
        if mobile:
            print(f"DEBUG: Trying primary match - name ilike '%{name}%' AND phone like '%{mobile}%' in dataset {dataset_id}")
            recipient = Recipient.query.filter(
                Recipient.dataset_id == dataset_id,
                Recipient.name.ilike(f'%{name}%'),
                Recipient.phone.like(f'%{mobile}%')
            ).first()
            print(f"DEBUG: Primary match result: {recipient}")
            if recipient:
                match_method = "name_and_mobile"
            
            # Try exact mobile match without wildcards
            if not recipient:
                print(f"DEBUG: Trying exact mobile match - phone = '{mobile}'")
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    Recipient.phone == mobile
                ).first()
                print(f"DEBUG: Exact mobile match result: {recipient}")
                if recipient:
                    match_method = "exact_mobile_with_name"
                
            # Try mobile match with ilike (case insensitive)
            if not recipient:
                print(f"DEBUG: Trying ilike mobile match")
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    Recipient.phone.ilike(f'%{mobile}%')
                ).first()
                print(f"DEBUG: ilike mobile match result: {recipient}")
                if recipient:
                    match_method = "ilike_mobile_with_name"
                
            # Try stripping whitespace and special characters from mobile
            if not recipient:
                clean_mobile = ''.join(filter(str.isdigit, mobile))
                print(f"DEBUG: Trying cleaned mobile '{clean_mobile}'")
                recipients_all = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id
                ).all()
                
                for r in recipients_all:
                    if r.phone:
                        clean_db_phone = ''.join(filter(str.isdigit, str(r.phone)))
                        print(f"DEBUG: Comparing '{clean_mobile}' with '{clean_db_phone}' for {r.name}")
                        if clean_mobile == clean_db_phone:
                            recipient = r
                            print(f"DEBUG: Found match with cleaned phone: {recipient}")
                            match_method = "cleaned_mobile_with_name"
                            break
            
            # Let's also try without the wildcard on mobile for exact match
            if not recipient:
                print(f"DEBUG: Trying fallback exact mobile match - phone = '{mobile}'")
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    Recipient.name.ilike(f'%{name}%'),
                    Recipient.phone == mobile
                ).first()
                print(f"DEBUG: Exact mobile match result: {recipient}")
                if recipient:
                    match_method = "fallback_exact_mobile"
         # Secondary match: exact name only
        if not recipient:
            print(f"DEBUG: Trying secondary match - name ilike '%{name}%' only in dataset {dataset_id}")
            recipient = Recipient.query.filter(
                Recipient.dataset_id == dataset_id,
                Recipient.name.ilike(f'%{name}%')
            ).first()
            print(f"DEBUG: Secondary match result: {recipient}")
            if recipient:
                match_method = "name_only"
        
        # Tertiary match: mobile number only (fallback when name check fails)
        if not recipient and mobile:
            print(f"DEBUG: Name check failed, trying mobile-only match - mobile: '{mobile}' in dataset {dataset_id}")
            
            # Try exact mobile match
            recipient = Recipient.query.filter(
                Recipient.dataset_id == dataset_id,
                Recipient.phone == mobile
            ).first()
            print(f"DEBUG: Mobile-only exact match result: {recipient}")
            if recipient:
                match_method = "mobile_only_exact"
            
            # Try mobile match with like operator
            if not recipient:
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    Recipient.phone.like(f'%{mobile}%')
                ).first()
                print(f"DEBUG: Mobile-only like match result: {recipient}")
                if recipient:
                    match_method = "mobile_only_like"
            
            # Try mobile match with ilike (case insensitive)
            if not recipient:
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    Recipient.phone.ilike(f'%{mobile}%')
                ).first()
                print(f"DEBUG: Mobile-only ilike match result: {recipient}")
                if recipient:
                    match_method = "mobile_only_ilike"
            
            # Try cleaned mobile number comparison
            if not recipient:
                clean_mobile = ''.join(filter(str.isdigit, mobile))
                print(f"DEBUG: Trying mobile-only with cleaned number: '{clean_mobile}'")
                recipients_all = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id
                ).all()
                
                for r in recipients_all:
                    if r.phone:
                        clean_db_phone = ''.join(filter(str.isdigit, str(r.phone)))
                        if clean_mobile == clean_db_phone:
                            recipient = r
                            print(f"DEBUG: Mobile-only cleaned match found: {recipient.name} - {recipient.phone}")
                            match_method = "mobile_only_cleaned"
                            break
        
        # Quaternary match: fuzzy name matching
        if not recipient:
            print(f"DEBUG: Trying quaternary match - fuzzy name matching in dataset {dataset_id}")
            # Try matching with partial names
            name_parts = name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                print(f"DEBUG: Fuzzy match - first: '{first_name}', last: '{last_name}'")
                recipient = Recipient.query.filter(
                    Recipient.dataset_id == dataset_id,
                    db.or_(
                        Recipient.name.ilike(f'%{first_name}%{last_name}%'),
                        Recipient.name.ilike(f'%{last_name}%{first_name}%')
                    )
                ).first()
                print(f"DEBUG: Quaternary match result: {recipient}")
                if recipient:
                    match_method = "fuzzy_name"

        if not recipient:
            # Let's also log all recipients in the selected dataset for debugging
            all_recipients = Recipient.query.filter(
                Recipient.dataset_id == dataset_id
            ).all()
            print(f"DEBUG: All recipients in dataset {dataset_id} ({dataset.hostel_name}):")
            for r in all_recipients:
                print(f"  - Name: '{r.name}' | Phone: '{r.phone}' | Dataset: {r.dataset_id}")
            
            return jsonify({
                'success': False,
                'message': f'No recipient found matching the scanned data in dataset "{dataset.hostel_name}". Name: {name}, Mobile: {mobile}. Please ensure you have selected the correct dataset.'
            })
        
        # Check current status and determine action
        current_status = recipient.status
        
        if scan_mode == 'checkin':
            new_status = 'Checked In'
            # Check if already checked in
            if current_status == 'Checked In':
                return jsonify({
                    'success': False,
                    'message': f'{recipient.name} is already checked in. Current status: {current_status}'
                })
        elif scan_mode == 'checkout':
            new_status = 'Checked Out'
            # Check if not checked in (can't check out if not checked in)
            if current_status != 'Checked In':
                return jsonify({
                    'success': False,
                    'message': f'{recipient.name} cannot be checked out because they are not checked in. Current status: {current_status}'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Invalid scan mode: {scan_mode}'
            })
        
        # Update recipient status
        recipient.status = new_status
        recipient.status_updated_at = datetime.now()
        db.session.commit()
        
        # Prepare success message based on match method
        if match_method.startswith("mobile_only"):
            match_info = f" (matched by mobile number: {mobile})"
        elif match_method == "name_only":
            match_info = f" (matched by name only)"
        elif match_method == "fuzzy_name":
            match_info = f" (matched by partial name)"
        else:
            match_info = ""
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'Successfully {"checked in" if scan_mode == "checkin" else "checked out"} {recipient.name} in room {recipient.room_no}{match_info}. Check your email for details.',
            'match_method': match_method,
            'recipient': {
                'name': recipient.name,
                'room_no': recipient.room_no,
                'hostel_allotted': recipient.hostel_allotted,
                'status': recipient.status,
                'email': recipient.email,
                'phone': recipient.phone
            }
        }
        
        # Get roommates if occupancy > 1
        roommates = Recipient.query.filter(
            Recipient.dataset_id == recipient.dataset_id,
            Recipient.room_no == recipient.room_no,
            Recipient.id != recipient.id
        ).all()
        
        if roommates:
            response_data['roommates'] = [
                {
                    'name': rm.name,
                    'phone': rm.phone,
                    'status': rm.status
                }
                for rm in roommates
            ]
        
        # Send email notification
        if recipient.email:
            try:
                send_room_notification_email(recipient, roommates, scan_mode)
            except Exception as e:
                print(f"Email sending failed: {e}")
                # Don't fail the entire operation if email fails
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"QR verification error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing QR scan: {str(e)}'
        })

def send_room_notification_email(recipient, roommates, scan_mode):
    """Send email notification with room details and roommate information."""
    from email_service import send_notification_email
    
    if scan_mode == "checkin":
        subject = f"Welcome to {recipient.hostel_allotted.upper()}!"
        action_text = f"Welcome to {recipient.hostel_allotted.upper()}!\n\nYou have been successfully checked in to Room {recipient.room_no}."
    else:
        subject = f"Check-out Confirmation - {recipient.hostel_allotted.upper()}"
        action_text = f"You have been successfully checked out from Room {recipient.room_no} at {recipient.hostel_allotted.upper()}."
    
    # Build roommate list
    roommate_info = ""
    if roommates:
        roommate_info = "\nYour Roommates:\n"
        for rm in roommates:
            status_text = "Checked In" if rm.status == "Checked In" else "Not Checked In Yet"
            phone_text = f" (Phone: {rm.phone})" if rm.phone else ""
            roommate_info += f"- {rm.name}{phone_text} - {status_text}\n"
    else:
        roommate_info = "\nYou have this room to yourself.\n"
    
    body = f"""Dear {recipient.name},

{action_text}

Your Details:
- Name: {recipient.name}
- Room Number: {recipient.room_no}
- Hostel: {recipient.hostel_allotted.upper()}
- Status: {recipient.status}
{roommate_info}
If you have any questions, please contact the hostel administration.

Best regards,
{recipient.hostel_allotted.upper()} Management"""
    
    send_notification_email(recipient.email, subject, body)

@app.route('/delete_dataset/<int:dataset_id>', methods=['POST'])
@login_required
def delete_dataset(dataset_id):
    """Delete a dataset and all associated recipients."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Verify the dataset belongs to user
        if dataset.user_id != user.id:
            flash('Unauthorized access')
            return redirect(url_for('datasets'))
        
        # Store the name for feedback message
        dataset_name = dataset.name
        
        # Delete dataset (recipients will be deleted via cascade)
        db.session.delete(dataset)
        db.session.commit()
        
        flash(f'Successfully deleted dataset "{dataset_name}" and all its recipients.')
        return redirect(url_for('datasets'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting dataset: {str(e)}')
        return redirect(url_for('datasets'))

# @app.route('/test-dashboard')
# @login_required
# def test_dashboard():
#     """Render the analytics dashboard page."""
#     user = User.query.filter_by(email=session['user_email']).first()
#     response = render_template('dashboard.html', user=user)
#     return add_no_cache_headers(response)

@app.route('/api/datasets')
@login_required
def api_datasets():
    """API endpoint to get user's datasets for dropdown selection."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        user_datasets = Dataset.query.filter_by(user_id=user.id).all()
        
        datasets_data = []
        for dataset in user_datasets:
            # Count recipients for each dataset
            recipients_count = Recipient.query.filter_by(dataset_id=dataset.id).count()
            
            datasets_data.append({
                'id': dataset.id,
                'hostel_name': dataset.hostel_name,
                'total_recipients': recipients_count,
                'floors': dataset.floors,
                'rooms_per_floor': dataset.rooms_per_floor
            })
        
        return jsonify(datasets_data)
        
    except Exception as e:
        print(f"Datasets API error: {e}")
        return jsonify({
            'error': 'Failed to load datasets',
            'message': str(e)
        }), 500

@app.route('/api/dashboard-analytics')
@login_required
def dashboard_analytics():
    """API endpoint to provide analytics data for the dashboard."""
    try:
        user = User.query.filter_by(email=session['user_email']).first()
        
        # Get dataset_id parameter for filtering
        dataset_id = request.args.get('dataset_id', type=int)
        
        # Get user's datasets (all or filtered by dataset_id)
        if dataset_id:
            user_datasets = Dataset.query.filter_by(user_id=user.id, id=dataset_id).all()
        else:
            user_datasets = Dataset.query.filter_by(user_id=user.id).all()
        
        dataset_ids = [d.id for d in user_datasets]
        
        if not dataset_ids:
            # Return empty data if no datasets
            return jsonify({
                'student_status': {
                    'checked_in': 0,
                    'not_checked_in': 0,
                    'checked_out': 0
                },
                'room_occupancy': {
                    'occupied': 0,
                    'remaining': 0,
                    'total': 0
                },
                'recent_activities': [],
                'statistics': {
                    'hostel_name': 'No Data',
                    'total_recipients': 0,
                    'checked_in': 0,
                    'checked_out': 0,
                    'total_rooms': 0,
                    'occupied_rooms': 0,
                    'occupancy_rate': 0
                }
            })
        
        all_recipients = Recipient.query.filter(Recipient.dataset_id.in_(dataset_ids)).all()
        
        # Calculate student status counts
        checked_in_count = len([r for r in all_recipients if r.status == 'Checked In'])
        not_checked_in_count = len([r for r in all_recipients if r.status == 'Not Checked In'])
        checked_out_count = len([r for r in all_recipients if r.status == 'Checked Out'])
        
        # Calculate room occupancy
        total_rooms = sum(d.rooms_per_floor * (d.floors + 1) for d in user_datasets)
        
        # Get unique occupied rooms (rooms with at least one checked-in person)
        occupied_rooms_set = set()
        for recipient in all_recipients:
            if recipient.status == 'Checked In':
                occupied_rooms_set.add((recipient.dataset_id, recipient.room_no))
        
        occupied_rooms = len(occupied_rooms_set)
        remaining_rooms = total_rooms - occupied_rooms
        
        # Get recent activities (last 10 check-ins/check-outs)
        # Sort by status_updated_at to get the most recent status changes
        recent_activities = []
        
        # Get recipients with recent status changes, sorted by most recent first
        recent_recipients = [r for r in all_recipients if r.status in ['Checked In', 'Checked Out']]
        recent_recipients.sort(key=lambda x: x.status_updated_at if x.status_updated_at else x.allocated_at, reverse=True)
        
        for recipient in recent_recipients[:10]:  # Limit to last 10 activities
            # Format timestamp
            timestamp = recipient.status_updated_at if recipient.status_updated_at else recipient.allocated_at
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'Unknown'
            
            recent_activities.append({
                'name': recipient.name,
                'room_no': recipient.room_no,
                'action': recipient.status,
                'timestamp': formatted_time
            })
        
        # Get hostel name (use first dataset's hostel name, or combine if multiple)
        hostel_names = list(set(d.hostel_name for d in user_datasets))
        hostel_name = hostel_names[0] if len(hostel_names) == 1 else f"{len(hostel_names)} Hostels"
        
        # Calculate occupancy rate
        occupancy_rate = round((occupied_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0
        
        # Prepare response data
        analytics_data = {
            'student_status': {
                'checked_in': checked_in_count,
                'not_checked_in': not_checked_in_count,
                'checked_out': checked_out_count
            },
            'room_occupancy': {
                'occupied': occupied_rooms,
                'remaining': remaining_rooms,
                'total': total_rooms
            },
            'recent_activities': recent_activities,
            'statistics': {
                'hostel_name': hostel_name,
                'total_recipients': len(all_recipients),
                'checked_in': checked_in_count,
                'checked_out': checked_out_count,
                'total_rooms': total_rooms,
                'occupied_rooms': occupied_rooms,
                'occupancy_rate': occupancy_rate
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        print(f"Dashboard analytics error: {e}")
        return jsonify({
            'error': 'Failed to load analytics data',
            'message': str(e)
        }), 500

# Health check endpoints
@app.route('/healthz')
def health_check():
    """Health check endpoint for Render and monitoring services."""
    try:
        # Test database connection using proper SQLAlchemy syntax
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return jsonify({
            'status': 'healthy',
            'service': 'dormease',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'dormease',
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 503

@app.route('/health')
def simple_health():
    """Simple health check endpoint."""
    return "System is Healthy, Flask App Operational", 200

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("notfound.html"), 404

if __name__ == '__main__':
    app.run(debug=False, port=3000)
