import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------
# Config
# -------------------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///arewa.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email config
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true','1','yes']

SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dev-salt-change-this')
ts = URLSafeTimedSerializer(app.secret_key)

db = SQLAlchemy(app)

# -------------------------
# Models
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10))
    password_hash = db.Column(db.String(256))
    vendor_business = db.Column(db.String(200))
    vendor_reg = db.Column(db.String(100))
    rider_vehicle = db.Column(db.String(100))
    rider_idno = db.Column(db.String(100))

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, pw)

# -------------------------
# Demo notifications store
# -------------------------
notifications_store = {'vendor': [], 'rider': [], 'customer': []}
_next_notification_id = 1
def push_notification(role, message, data=None):
    global _next_notification_id
    role = role if role in notifications_store else 'vendor'
    item = {'id': _next_notification_id, 'message': message, 'ts': datetime.utcnow().isoformat()+'Z', 'data': data or {}}
    notifications_store[role].append(item)
    _next_notification_id += 1
    return item

# -------------------------
# Helpers: send email (SMTP or console fallback)
# -------------------------
def send_email(subject: str, recipient: str, body: str):
    if MAIL_USERNAME and MAIL_PASSWORD and MAIL_SERVER:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = MAIL_USERNAME
            msg['To'] = recipient
            msg.set_content(body)
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as smtp:
                if MAIL_USE_TLS:
                    smtp.starttls()
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
            app.logger.info("Email sent to %s", recipient)
            return True
        except Exception as e:
            app.logger.error("SMTP error: %s", e)
    # fallback: console
    print("=== EMAIL (console fallback) ===")
    print("To:", recipient)
    print("Subject:", subject)
    print(body)
    print("=== END EMAIL ===")
    return False

# -------------------------
# Utils: token for reset
# -------------------------
def generate_password_reset_token(email):
    return ts.dumps(email, salt=SECURITY_PASSWORD_SALT)

def confirm_password_reset_token(token, expiration=3600):
    try:
        email = ts.loads(token, salt=SECURITY_PASSWORD_SALT, max_age=expiration)
    except Exception:
        return None
    return email

# -------------------------
# Routes
# -------------------------
@app.route('/')
def index():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    fullname = request.form.get('fullname','').strip()
    email = request.form.get('email','').strip().lower()
    phone = request.form.get('phone','').strip()
    role = request.form.get('role')
    password = request.form.get('password')

    if not email or not password:
        flash("Email and password required.")
        return redirect(url_for('register'))

    if User.query.filter_by(email=email).first():
        flash("Email already registered. Try login or forgot password.")
        return redirect(url_for('register'))

    verification_code = "123456"  # demo OTP

    u = User(fullname=fullname, email=email, phone=phone, role=role, verification_code=verification_code)
    if role == 'vendor':
        u.vendor_business = request.form.get('vendor_business')
        u.vendor_reg = request.form.get('vendor_reg')
    if role == 'rider':
        u.rider_vehicle = request.form.get('rider_vehicle')
        u.rider_idno = request.form.get('rider_idno')
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    session['user_id'] = u.id

    # Send verification code (console/email)
    subj = "ArewaDeliver — verification code"
    body = f"Hello {u.fullname or u.email},\nYour verification code is: {verification_code}\n\nThanks,\nArewaDeliver"
    send_email(subj, u.email, body)
    return redirect(url_for('verify'))

# Verify
@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'GET':
        return render_template('verify.html')
    code = request.form.get('code','').strip()
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired, please register/login again.")
        return redirect(url_for('register'))
    user = User.query.get(user_id)
    if user and user.verification_code == code:
        user.is_verified = True
        db.session.commit()
        session['role'] = user.role
        session['email'] = user.email
        return redirect(url_for('welcome', role=user.role))
    flash("Invalid code")
    return redirect(url_for('verify'))

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session.clear()
        session['user_id'] = user.id
        session['role'] = user.role
        session['email'] = user.email
        return redirect(url_for('welcome', role=user.role))
    flash("Invalid credentials")
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Forgot password
@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'GET':
        return render_template('forgot.html')
    email = request.form.get('email','').strip().lower()
    if not email:
        flash("Provide email")
        return redirect(url_for('forgot'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("If the email exists, instructions have been sent.")
        return redirect(url_for('login'))
    token = generate_password_reset_token(user.email)
    reset_url = url_for('reset_with_token', token=token, _external=True)
    body = render_template('email/reset_email.txt', reset_url=reset_url, user=user)
    send_email("Reset your ArewaDeliver password", user.email, body)
    flash("If the email exists, instructions have been sent.")
    return redirect(url_for('login'))

# Reset
@app.route('/reset/<token>', methods=['GET','POST'])
def reset_with_token(token):
    email = confirm_password_reset_token(token)
    if not email:
        flash("Invalid/expired link")
        return redirect(url_for('forgot'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid user")
        return redirect(url_for('forgot'))
    if request.method == 'POST':
        newpw = request.form.get('password')
        if not newpw or len(newpw) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('reset_with_token', token=token))
        user.set_password(newpw)
        db.session.commit()
        flash("Password updated. Please login.")
        return redirect(url_for('login'))
    return render_template('reset.html', token=token)

# Welcome
@app.route('/welcome/<role>')
def welcome(role):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login first.")
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if not user or not user.is_verified:
        flash("Complete verification first.")
        return redirect(url_for('verify'))
    return render_template('welcome.html', message="Welcome to ArewaDeliver! Your account is verified and ready.", role=user.role)

# Dashboard helpers
def require_login():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

@app.route('/customer_dashboard')
def customer_dashboard():
    user = require_login()
    if not user or user.role != 'customer':
        flash("Login as customer.")
        return redirect(url_for('login'))
    return render_template('customer_dashboard.html', user=user)

@app.route('/vendor_dashboard')
def vendor_dashboard():
    user = require_login()
    if not user or user.role != 'vendor':
        flash("Login as vendor.")
        return redirect(url_for('login'))
    return render_template('vendor_dashboard.html', user=user)

@app.route('/rider_dashboard')
def rider_dashboard():
    user = require_login()
    if not user or user.role != 'rider':
        flash("Login as rider.")
        return redirect(url_for('login'))
    return render_template('rider_dashboard.html', user=user)

# Notifications API (demo)
@app.route('/notifications', methods=['GET'])
def get_notifications():
    user = require_login()
    if not user:
        return jsonify({'ok': False, 'error': 'not_logged_in'}), 401
    role = user.role
    notes = notifications_store.get(role, [])
    notifications_store[role] = []
    return jsonify({'ok': True, 'notifications': notes})

@app.route('/notify', methods=['POST'])
def add_notification():
    data = request.get_json(force=True)
    role = data.get('role','vendor')
    message = data.get('message','New notification')
    item = push_notification(role, message, data.get('data'))
    return jsonify({'ok': True, 'notification': item})

# Debug
@app.route('/_debug/notifications')
def debug_notifications():
    return jsonify(notifications_store)

# Bootstrap & run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)