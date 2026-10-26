import os
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash

from models import db, User, BloodInventory, Reservation, DonationHistory, Notification
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
        last_donation_date_str = request.form.get('last_donation_date')
        
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
        
        if role == 'donor' and last_donation_date_str:
            try:
                last_date = datetime.strptime(last_donation_date_str, '%Y-%m-%d')
                past_donation = DonationHistory(
                    donor_id=new_user.id,
                    units_donated=0,
                    donation_date=last_date,
                    status='Previous'
                )
                db.session.add(past_donation)
                db.session.commit()
            except ValueError:
                pass # Ignore if date format is invalid or empty
        
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
    
    # Donation Chart Data (last 7 days)
    today = datetime.now(timezone.utc)
    chart_labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    chart_values = []
    for date_str in chart_labels:
        count = db.session.query(db.func.sum(DonationHistory.units_donated)).filter(
            db.func.strftime('%Y-%m-%d', DonationHistory.donation_date) == date_str
        ).scalar() or 0
        chart_values.append(int(count))

    # Blood Group Distribution Data
    distribution = db.session.query(BloodInventory.blood_group, db.func.sum(BloodInventory.units)).group_by(BloodInventory.blood_group).all()
    dist_labels = [row[0] for row in distribution]
    dist_values = [int(row[1]) for row in distribution]

    return render_template('admin_dashboard.html', 
        inventory=inventory_items, 
        total_donations=total_donations, 
        total_users=total_users,
        expiring_soon=expiring_soon,
        pending_requests=pending,
        recent_donations=recent_donations,
        recent_users=recent_users,
        chart_labels=chart_labels,
        chart_values=chart_values,
        dist_labels=dist_labels,
        dist_values=dist_values,
        notifications=Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    )

@app.route('/dashboard/donor')
@login_required('donor')
def donor_dashboard():
    user = db.session.get(User, session['user_id'])
    history = DonationHistory.query.filter_by(donor_id=user.id).order_by(DonationHistory.donation_date.desc()).all()
    
    # Eligibility calculation (90 days rule)
    eligible_to_donate = True
    days_since_last = -1
    if history:
        last_donation = history[0].donation_date
        days_since_last = (datetime.utcnow() - last_donation).days
        if days_since_last < 90:
            eligible_to_donate = False
            
    lives_saved = sum(h.units_donated for h in history) if history else 0
    lives_saved *= 3 # Estimate 1 unit = 3 lives
            
    return render_template('donor_dashboard.html', 
        user=user, history=history, 
        eligible=eligible_to_donate, days_since_last=days_since_last, lives_saved=lives_saved,
        notifications=Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    )

@app.route('/dashboard/receiver')
@login_required('receiver')
def receiver_dashboard():
    user = db.session.get(User, session['user_id'])
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template('receiver_dashboard.html', user=user, reservations=reservations, notifications=notifications)

@app.route('/dashboard/hospital')
@login_required('hospital')
def hospital_dashboard():
    user = db.session.get(User, session['user_id'])
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template('hospital_dashboard.html', user=user, reservations=reservations, notifications=notifications)

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
    user = db.session.get(User, session['user_id'])
    units_to_donate = int(request.form.get('units', 1))
    
    if units_to_donate < 1 or units_to_donate > 3:
        flash("You can donate between 1 and 3 units.", "warning")
        return redirect(url_for('dashboard'))
    
    # Security: check eligibility again
    history = DonationHistory.query.filter_by(donor_id=user.id).order_by(DonationHistory.donation_date.desc()).first()
    if history:
        days_since_last = (datetime.utcnow() - history.donation_date).days
        if days_since_last < 90:
            flash("Not eligible to donate yet. 90-day cooldown period active.", "danger")
            return redirect(url_for('dashboard'))
            
    # Add to history
    new_donation = DonationHistory(donor_id=user.id, units_donated=units_to_donate, status='Completed')
    db.session.add(new_donation)
    
    # Update inventory pool
    city = user.city if user.city else 'Headquarters'
    bg = user.blood_group
    
    inv = BloodInventory.query.filter_by(blood_group=bg, city=city).first()
    if inv:
        inv.units += units_to_donate
    else:
        # Blood expires in 35 days standard
        inv = BloodInventory(
            blood_group=bg, city=city, units=units_to_donate,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=35)
        )
        db.session.add(inv)
        
    db.session.commit()
    flash(f"Thank you for donating {units_to_donate} unit(s)! The inventory has been updated.", "success")
    return redirect(url_for('dashboard'))

@app.route('/approve_request/<int:req_id>', methods=['POST'])
@login_required('admin')
def approve_request(req_id):
    req = db.session.get(Reservation, req_id)
    if not req or req.status not in ['Pending', 'Accepted Alternative']:
        flash("Request not found or already processed.", "warning")
        return redirect(url_for('dashboard'))
        
    bg = req.suggested_blood_group if req.status == 'Accepted Alternative' else req.blood_group
    
    inv_items = BloodInventory.query.filter_by(blood_group=bg).order_by(BloodInventory.expiry_date.asc()).all()
    units_needed = req.units
    
    available_units = sum(item.units for item in inv_items)
    
    if available_units >= units_needed:
        for item in inv_items:
            if units_needed <= 0:
                break
            if item.units > 0:
                take = min(item.units, units_needed)
                item.units -= take
                units_needed -= take
        req.status = 'Approved'
        db.session.commit()
        
        # Notify user of approval
        msg = f"Your request {req.unique_id} for {bg} has been approved. Please collect it from the inventory."
        notif = Notification(user_id=req.user_id, message=msg)
        db.session.add(notif)
        db.session.commit()
        
        flash(f"Request {req.unique_id} approved. Inventory auto-deducted.", "success")
    else:
        # If Pending and direct blood not available, find compatible alternatives
        if req.status == 'Pending':
            compatible_groups = get_compatible_blood_types(req.blood_group)
            found_alt = False
            for alt_bg in compatible_groups:
                if alt_bg == req.blood_group: continue
                
                alt_inv = db.session.query(db.func.sum(BloodInventory.units)).filter_by(blood_group=alt_bg).scalar() or 0
                if alt_inv >= req.units:
                    req.status = 'Alternative Suggested'
                    req.suggested_blood_group = alt_bg
                    req.suggested_units = req.units
                    
                    # Notify user
                    notif = Notification(
                        user_id=req.user_id,
                        message=f"Required blood {req.blood_group} is in shortage. We suggest {alt_bg} as a compatible alternative for your request {req.unique_id}."
                    )
                    db.session.add(notif)
                    db.session.commit()
                    flash(f"Shortage of {req.blood_group}. Alternative {alt_bg} suggested to user.", "info")
                    found_alt = True
                    break
            
            if not found_alt:
                flash(f"Not enough {req.blood_group} or compatible blood available in the nationwide inventory.", "danger")
        else:
            flash(f"Not enough units available to fulfill the alternative request.", "danger")
        
    return redirect(url_for('dashboard'))

@app.route('/accept_alternative/<int:req_id>', methods=['POST'])
@login_required()
def accept_alternative(req_id):
    req = db.session.get(Reservation, req_id)
    if not req or req.user_id != session['user_id'] or req.status != 'Alternative Suggested':
        flash("Invalid request or unauthorized.", "danger")
        return redirect(url_for('dashboard'))
    
    req.status = 'Accepted Alternative'
    
    # Notify Admin that user accepted the alternative
    admin = User.query.filter_by(role='admin').first()
    if admin:
        admin_notif = Notification(
            user_id=admin.id,
            message=f"User {session.get('user_name')} accepted alternative {req.suggested_blood_group} for request {req.unique_id}. You can now approve it."
        )
        db.session.add(admin_notif)
    
    db.session.commit()
    
    flash("You have accepted the alternative blood type. Admin will finalize the request shortly.", "success")
    return redirect(url_for('dashboard'))

@app.route('/mark_notification_read/<int:notif_id>', methods=['POST'])
@login_required()
def mark_notification_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == session['user_id']:
        notif.is_read = True
        db.session.commit()
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
