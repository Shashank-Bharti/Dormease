from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Models
class User(db.Model):
    """User model for storing user account information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<User {self.email}>'

# OTP store (in-memory) 
otp_store = {}
