from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Models
class User(db.Model):
    """User model for storing user account information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    
    # Relationship with datasets
    datasets = db.relationship('Dataset', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Dataset(db.Model):
    """Dataset model for storing uploaded CSV information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    hostel_name = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    floors = db.Column(db.Integer, nullable=False)
    rooms_per_floor = db.Column(db.Integer, nullable=False)
    occupancy_per_room = db.Column(db.Integer, nullable=False)
    extra_info = db.Column(db.Text)
    total_capacity = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship with recipients
    recipients = db.relationship('Recipient', backref='dataset', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Dataset {self.name}>'

class Recipient(db.Model):
    """Recipient model for storing individual recipient information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    room_no = db.Column(db.String(10), nullable=False)
    hostel_allotted = db.Column(db.String(200), nullable=False)    
    status = db.Column(db.String(20), default='Not Checked In')  # 'Checked In', 'Not Checked In', or 'Checked Out'
    allocated_at = db.Column(db.DateTime, default=datetime.now)
    status_updated_at = db.Column(db.DateTime, default=datetime.now)  # Track when status was last updated
    
    # Additional fields from CSV
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    
    # Foreign key to dataset
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    
    def __repr__(self):
        return f'<Recipient {self.name} - Room {self.room_no}>'

# OTP store (in-memory) 
otp_store = {}
