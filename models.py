from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'donor', 'receiver', 'hospital'
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    blood_group = db.Column(db.String(5), nullable=True) # A+, O-, etc.
    city = db.Column(db.String(100), nullable=True)
    certificate_path = db.Column(db.String(255), nullable=True) # Path to health certs
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'
    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    units = db.Column(db.Integer, nullable=False, default=0)
    added_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expiry_date = db.Column(db.DateTime, nullable=False)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False) # e.g., RES-2026-AB123
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    priority_level = db.Column(db.String(20), nullable=False, default='Normal') # Emergency, Critical, Surgery, Normal
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Approved, Ready, Completed
    request_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    suggested_blood_group = db.Column(db.String(5), nullable=True)
    suggested_units = db.Column(db.Integer, nullable=True)
    
    user = db.relationship('User', backref=db.backref('reservations', lazy=True))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

class DonationHistory(db.Model):
    __tablename__ = 'donation_history'
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    units_donated = db.Column(db.Integer, nullable=False)
    donation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Completed')
    
    donor = db.relationship('User', backref=db.backref('donations', lazy=True))
