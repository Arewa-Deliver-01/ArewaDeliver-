from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "arewa_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arewa.db'
db = SQLAlchemy(app)

# -----------------------------
# DATABASE MODEL
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(50))  # customer, vendor, rider
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10))

# -----------------------------
# HOME
# -----------------------------
@app.route('/')
def home():
    return "ArewaDelivery API Running..."

# -----------------------------
# REGISTRATION PAGE
# -----------------------------
@app.route('/register')
def register_page():
    return render_template('register.html')

# -----------------------------
# REGISTER USER
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    phone = request.form['phone']
    role = request.form['role']

    # Create fake verification code (in real life send SMS/Email)
    verification_code = "123456"

    new_user = User(email=email, phone=phone, role=role, verification_code=verification_code)
    db.session.add(new_user)
    db.session.commit()

    # Store session
    session['user_id'] = new_user.id

    # Go to verification page
    return redirect(url_for('verify_page'))

# -----------------------------
# VERIFICATION PAGE
# -----------------------------
@app.route('/verify')
def verify_page():
    return render_template('verify.html')

# -----------------------------
# VERIFY USER
# -----------------------------
@app.route('/verify', methods=['POST'])
def verify():
    input_code = request.form.get('code')
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if user and user.verification_code == input_code:
        user.is_verified = True
        db.session.commit()

        # Redirect based on role
        return redirect(url_for('welcome', role=user.role))
    else:
        return "Invalid verification code. Try again."

# -----------------------------
# WELCOME PAGE BASED ON ROLE
# -----------------------------
@app.route('/welcome/<role>')
def welcome(role):
    role = role.lower()

    if role == 'customer':
        message = "Welcome to Arewa Delivery! Your account is verified and ready. Enjoy fast, secure and reliable deliveries anytime."

    elif role == 'vendor':
        message = (
            "Welcome to ArewaDelivery Vendor Network! Your account has been verified. "
            "Please complete your profile to activate your store so you can start receiving delivery orders immediately."
        )

    elif role == 'rider':
        message = (
            "Welcome to ArewaDelivery Riders Team! Your account has been verified. "
            "Complete your KYC and registration payment to activate your dashboard and start accepting delivery tasks."
        )

    else:
        message = "Welcome to Arewa Delivery!"

    return render_template('welcome.html', message=message, role=role)

# -----------------------------
# RUN
# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
app.run(debug=True)

@app.route('/welcome/<role>')
def welcome(role):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('register_page'))  # redirect if no session

    role = role.lower()
    user = User.query.get(user_id)
    if not user or not user.is_verified:
        return redirect(url_for('verify_page'))  # redirect if not verified

    if role == 'customer':
        message = "Welcome to Arewa Delivery! Your account is verified and ready. Enjoy fast, secure and reliable deliveries anytime."
    elif role == 'vendor':
        message = ("Welcome to ArewaDelivery Vendor Network! Your account has been verified. "
                   "Please complete your profile to activate your store and start receiving delivery orders immediately.")
    elif role == 'rider':
        message = ("Welcome to ArewaDelivery Riders Team! Your account has been verified. "
                   "Complete your KYC and registration payment to activate your dashboard and start accepting delivery tasks.")
    else:
        message = "Welcome to Arewa Delivery!"

    return render_template('welcome.html', message=message, role=user.role)
