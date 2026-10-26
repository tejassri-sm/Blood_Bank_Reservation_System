import os
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash

from models import db, User, BloodInventory, Reservation, DonationHistory
from functools import wraps

app = Flask(__name__)
# Database & App Config
app.config['SECRET_KEY'] = 'premium_blood_bank_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blood_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

db.init_app(app)

# Helper: Role-based Access Control Decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "danger")
                return redirect(url_for('login'))
            if role and session.get('user_role') != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Helper: Smart Compatibility Engine
def get_compatible_blood_types(blood_group):
    """
    Returns a list of blood groups that can be given to a receiver with `blood_group`.
    """
    compatibility = {
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'O+': ['O+', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'O-': ['O-'],
        'B-': ['B-', 'O-'],
        'AB-': ['AB-', 'A-', 'B-', 'O-'],
        'Bombay': ['Bombay'] # Rare blood group registry feature
    }
    return compatibility.get(blood_group, [])

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

# ================= ROUTES ================= 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        blood_group = request.form.get('blood_group')
        city = request.form.get('city')
        
        # Prevent Fraud/Duplicate Detection
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))
        
        new_user = User(
            name=name, email=email, role=role, 
            blood_group=blood_group, city=city
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful. Proceed to login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.name
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out securely.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required()
def dashboard():
    role = session.get('user_role')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'donor':
        return redirect(url_for('donor_dashboard'))
    elif role == 'receiver':
        return redirect(url_for('receiver_dashboard'))
    elif role == 'hospital':
        return redirect(url_for('hospital_dashboard'))
    return redirect(url_for('index'))

# ================= DASHBOARDS ================= 

@app.route('/dashboard/admin')
@login_required('admin')
def admin_dashboard():
    # Admin Analytics Dashboard Feature
    total_donations = db.session.query(db.func.sum(DonationHistory.units_donated)).scalar() or 0
    total_users = User.query.count()
    inventory_items = BloodInventory.query.all()
    # Check for expiring blood (within 5 days)
    five_days_from_now = datetime.now(timezone.utc) + timedelta(days=5)
    expiring_soon = BloodInventory.query.filter(BloodInventory.expiry_date <= five_days_from_now).all()
    
    # Priority Queue System
    pending = Reservation.query.filter_by(status='Pending').all()
    priority_order = {'Emergency': 0, 'Critical': 1, 'Surgery': 2, 'Normal': 3}
    pending.sort(key=lambda x: priority_order.get(x.priority_level, 4))
    
    # Recent Activity Data
    recent_donations = DonationHistory.query.order_by(DonationHistory.donation_date.desc()).limit(15).all()
    recent_users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).limit(15).all()
    
    return render_template('admin_dashboard.html', 
        inventory=inventory_items, 
        total_donations=total_donations, 
        total_users=total_users,
        expiring_soon=expiring_soon,
        pending_requests=pending,
        recent_donations=recent_donations,
        recent_users=recent_users
    )

@app.route('/dashboard/donor')
@login_required('donor')
def donor_dashboard():
    user = User.query.get(session['user_id'])
    history = DonationHistory.query.filter_by(donor_id=user.id).order_by(DonationHistory.donation_date.desc()).all()
    
    # Eligibility calculation (90 days rule)
    eligible_to_donate = True
    days_since_last = -1
    if history:
        last_donation = history[0].donation_date
        days_since_last = (datetime.now(timezone.utc) - last_donation).days
        if days_since_last < 90:
            eligible_to_donate = False
            
    lives_saved = sum(h.units_donated for h in history) if history else 0
    lives_saved *= 3 # Estimate 1 unit = 3 lives
            
    return render_template('donor_dashboard.html', 
        user=user, history=history, 
        eligible=eligible_to_donate, days_since_last=days_since_last, lives_saved=lives_saved
    )

@app.route('/dashboard/receiver')
@login_required('receiver')
def receiver_dashboard():
    user = User.query.get(session['user_id'])
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template('receiver_dashboard.html', user=user, reservations=reservations)

@app.route('/dashboard/hospital')
@login_required('hospital')
def hospital_dashboard():
    user = User.query.get(session['user_id'])
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template('hospital_dashboard.html', user=user, reservations=reservations)

# ================= API / ACTIONS ================= 

@app.route('/search_blood', methods=['GET'])
def search_blood():
    # Nationwide Blood availability system & advanced filter
    blood_group = request.args.get('blood_group')
    city = request.args.get('city')
    
    query = BloodInventory.query
    if blood_group:
        # Smart Compatibility Engine
        compatible = get_compatible_blood_types(blood_group)
        if compatible:
            query = query.filter(BloodInventory.blood_group.in_(compatible))
    if city:
        query = query.filter(BloodInventory.city.ilike(f'%{city}%'))
        
    results = query.all()
    return jsonify([{
        'id': item.id,
        'blood_group': item.blood_group,
        'city': item.city,
        'units': item.units,
        'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
    } for item in results])

@app.route('/request_blood', methods=['POST'])
@login_required()
def request_blood():
    user_id = session['user_id']
    blood_group = request.form.get('blood_group')
    units = int(request.form.get('units'))
    priority = request.form.get('priority', 'Normal') # Emergency, Critical, Surgery, Normal
    
    # Unique Reservation Tracking System
    unique_id = f"RES-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}{blood_group.replace('+','P').replace('-','N')}"
    
    new_res = Reservation(
        unique_id=unique_id, user_id=user_id, blood_group=blood_group,
        units=units, priority_level=priority
    )
    db.session.add(new_res)
    db.session.commit()
    
    flash(f"Blood request submitted successfully. Tracker ID: {unique_id}", "success")
    return redirect(url_for('dashboard'))

@app.route('/donate_blood', methods=['POST'])
@login_required('donor')
def donate_blood():
    user = User.query.get(session['user_id'])
    
    # Security: check eligibility again
    history = DonationHistory.query.filter_by(donor_id=user.id).order_by(DonationHistory.donation_date.desc()).first()
    if history:
        days_since_last = (datetime.now(timezone.utc) - history.donation_date).days
        if days_since_last < 90:
            flash("Not eligible to donate yet. 90-day cooldown period active.", "danger")
            return redirect(url_for('dashboard'))
            
    # Add to history
    new_donation = DonationHistory(donor_id=user.id, units_donated=1, status='Completed')
    db.session.add(new_donation)
    
    # Update inventory pool
    city = user.city if user.city else 'Headquarters'
    bg = user.blood_group
    
    inv = BloodInventory.query.filter_by(blood_group=bg, city=city).first()
    if inv:
        inv.units += 1
    else:
        # Blood expires in 35 days standard
        inv = BloodInventory(
            blood_group=bg, city=city, units=1,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=35)
        )
        db.session.add(inv)
        
    db.session.commit()
    flash("Thank you for your life-saving donation! The inventory has been updated.", "success")
    return redirect(url_for('dashboard'))

@app.route('/approve_request/<int:req_id>', methods=['POST'])
@login_required('admin')
def approve_request(req_id):
    req = db.session.get(Reservation, req_id)
    if not req or req.status != 'Pending':
        flash("Request not found or already processed.", "warning")
        return redirect(url_for('dashboard'))
        
    # National Search / Prioritization Logic Checks Inventory
    bg = req.blood_group
    inv_items = BloodInventory.query.filter_by(blood_group=bg).order_by(BloodInventory.expiry_date.asc()).all()
    
    units_needed = req.units
    
    for item in inv_items:
        if units_needed <= 0:
            break
        if item.units > 0:
            take = min(item.units, units_needed)
            item.units -= take
            units_needed -= take
            
    if units_needed <= 0:
        req.status = 'Approved'
        db.session.commit()
        flash(f"Request {req.unique_id} approved. Inventory auto-deducted.", "success")
    else:
        db.session.rollback()
        flash(f"Not enough {bg} blood available in the nationwide inventory to fulfill this request.", "danger")
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed database with rare blood groups and admin if empty
        if User.query.count() == 0:
            # Create an admin account by default
            admin = User(name="System Admin", email="admin@bloodbank.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Database initialized. Default admin: admin@bloodbank.com / admin123")
            
    app.run(debug=True, port=5000)
