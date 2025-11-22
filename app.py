# app.py
import os
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------
# Configuration
# -------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arewa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email config from environment (optional)
MAIL_SERVER = os.environ.get('MAIL_SERVER')          # e.g. "smtp.gmail.com"
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')      # your Gmail address
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')      # app password or actual password (app password recommended)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']

# Token serializer
SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dev-salt-change-this')
ts = URLSafeTimedSerializer(app.secret_key)

db = SQLAlchemy(app)

# -------------------------
# Database model (updated)
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(50))  # customer, vendor, rider
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10))
    password_hash = db.Column(db.String(256))
    # vendor / rider extra fields (optional)
    vendor_business = db.Column(db.String(200))
    vendor_reg = db.Column(db.String(100))
    rider_vehicle = db.Column(db.String(100))
    rider_idno = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

# -------------------------
# Helpers: email sending
# -------------------------
def send_email(subject: str, recipient: str, body: str):
    """
    Send email via SMTP if MAIL_USERNAME/MAIL_PASSWORD configured.
    Otherwise print the message to console for development.
    """
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
            app.logger.info(f"Sent email to {recipient} via SMTP.")
            return True
        except Exception as e:
            app.logger.error("Failed to send email via SMTP: %s", e)
            # fallback to console
    # Console fallback
    print("==== EMAIL (console fallback) ====")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(body)
    print("==================================")
    return False

# -------------------------
# Routes
# -------------------------
@app.route('/')
def home():
    return "ArewaDelivery API Running..."

# Registration page (GET) uses template
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Register user (POST)
@app.route('/register', methods=['POST'])
def register():
    fullname = request.form.get('fullname', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    role = request.form.get('role')
    password = request.form.get('password')

    # Basic validation
    if not email or not password:
        flash("Email and password required.")
        return redirect(url_for('register_page'))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("Account with this email already exists. Please login or use forgot password.")
        return redirect(url_for('register_page'))

    # create verification code for demo (in prod generate random code/send email)
    verification_code = "123456"

    user = User(
        fullname=fullname,
        email=email,
        phone=phone,
        role=role,
        verification_code=verification_code
    )

    # store extra fields (vendor/rider)
    if role == 'vendor':
        user.vendor_business = request.form.get('vendor_business')
        user.vendor_reg = request.form.get('vendor_reg')
    if role == 'rider':
        user.rider_vehicle = request.form.get('rider_vehicle')
        user.rider_idno = request.form.get('rider_idno')

    # set hashed password
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Save user_id into session for verify flow
    session['user_id'] = user.id

    # Send verification email (demo contains the code)
    subject = "ArewaDeliver — Your verification code"
    body = f"Hello {user.fullname or user.email},\n\nYour verification code: {verification_code}\n\nIf you didn't register, ignore this email."
    send_email(subject, user.email, body)

    # Redirect to verify
    return redirect(url_for('verify_page'))

# Verify page
@app.route('/verify', methods=['GET'])
def verify_page():
    return render_template('verify.html')

# Verify POST
@app.route('/verify', methods=['POST'])
def verify():
    input_code = request.form.get('code', '').strip()
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired — please login or register again.")
        return redirect(url_for('register_page'))

    user = User.query.get(user_id)
    if user and user.verification_code == input_code:
        user.is_verified = True
        db.session.commit()

        # create session and redirect to welcome
        session['user_id'] = user.id
        session['role'] = user.role
        session['email'] = user.email
        return redirect(url_for('welcome', role=user.role))
    else:
        flash("Invalid verification code.")
        return redirect(url_for('verify_page'))

# LOGIN (simple)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['role'] = user.role
        session['email'] = user.email
        return redirect(url_for('welcome', role=user.role))
    else:
        flash("Invalid login credentials.")
        return redirect(url_for('login'))

# -------------------------
# FORGOT / RESET password
# -------------------------
def generate_password_reset_token(email):
    return ts.dumps(email, salt=SECURITY_PASSWORD_SALT)

def confirm_password_reset_token(token, expiration=3600):
    try:
        email = ts.loads(token, salt=SECURITY_PASSWORD_SALT, max_age=expiration)
    except Exception:
        return None
    return email

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'GET':
        return render_template('forgot.html')

    email = request.form.get('email', '').strip().lower()
    if not email:
        flash("Please provide your email address.")
        return redirect(url_for('forgot'))

    user = User.query.filter_by(email=email).first()
    if not user:
        # Do not reveal whether the email exists — generic message
        flash("If the email is registered, you will receive instructions.")
        return redirect(url_for('forgot'))

    # Generate token
    token = generate_password_reset_token(user.email)
    reset_url = url_for('reset_with_token', token=token, _external=True)

    # send email (or print to console)
    subject = "Reset your ArewaDeliver password"
    email_body = render_template('email/reset_email.txt', reset_url=reset_url, user=user)
    send_email(subject, user.email, email_body)

    flash("If that email is registered, a password reset link has been sent.")
    return redirect(url_for('login'))

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    email = confirm_password_reset_token(token)
    if not email:
        flash("The password reset link is invalid or has expired.")
        return redirect(url_for('forgot'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid user.")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for('reset_with_token', token=token))
        user.set_password(new_password)
        db.session.commit()
        flash("Your password has been updated. Please login.")
        return redirect(url_for('login'))

    return render_template('reset.html', token=token)

# WELCOME route (protected)
@app.route('/welcome/<role>')
def welcome(role):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login first.")
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user or not user.is_verified:
        flash("Please complete verification.")
        return redirect(url_for('verify_page'))

    # Role is from session/user, ignore the role param validation risk
    return render_template('welcome.html', message=(
        "Welcome to ArewaDelivery! Your account is verified and ready."
    ), role=user.role)

# -------------------------
# Utility: logout
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------------
# Bootstrap DB & run
# -------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
