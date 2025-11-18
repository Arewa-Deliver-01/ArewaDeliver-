from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# -----------------------------
# DATABASE SETUP
# -----------------------------
def get_db():
    conn = sqlite3.connect('arewadeliver.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    # Users: customer, vendor, rider, platform (id=0)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            profile_image TEXT DEFAULT 'default.png',
            wallet_balance REAL DEFAULT 0
        )
    """)

    # Transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,       -- credit or debit
            category TEXT,   -- payment, delivery fee, commission, notification
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            vendor_id INTEGER,
            rider_id INTEGER,
            product_amount REAL,
            delivery_fee REAL,
            status TEXT DEFAULT 'pending',  -- pending, paid, delivered
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create platform wallet if not exists
    cursor.execute("SELECT * FROM users WHERE id=0")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (id, role, name) VALUES (0, 'platform', 'ArewaDeliver Platform')")

    conn.commit()
    conn.close()

create_tables()

# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/customer')
def customer_profile():
    return render_template("customer.html")

@app.route('/vendor')
def vendor_profile():
    return render_template("vendor.html")

@app.route('/rider')
def rider_profile():
    return render_template("rider.html")

# Save user profile
@app.route('/save_profile', methods=['POST'])
def save_profile():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (role, name, phone, email, address)
        VALUES (?, ?, ?, ?, ?)
    """, (data['role'], data['name'], data['phone'], data['email'], data['address']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Profile saved successfully"})

# Wallet endpoints
@app.route('/wallet_transaction', methods=['POST'])
def wallet_transaction():
    data = request.json
    user_id = data['user_id']
    amount = float(data['amount'])
    tx_type = data['type']

    conn = get_db()
    cursor = conn.cursor()

    # Get current balance
    cursor.execute("SELECT wallet_balance FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"status":"error", "message":"User not found"})
    
    current_balance = row['wallet_balance']
    new_balance = current_balance + amount if tx_type=="credit" else current_balance - amount

    if new_balance < 0:
        return jsonify({"status":"error", "message":"Insufficient balance"})

    # Update balance
    cursor.execute("UPDATE users SET wallet_balance=? WHERE id=?", (new_balance, user_id))

    # Insert transaction
    cursor.execute("INSERT INTO transactions (user_id, amount, type, category) VALUES (?,?,?,?)",
                   (user_id, amount, tx_type, "manual"))

    conn.commit()

    # Return all transactions
    cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,))
    transactions = [dict(tx) for tx in cursor.fetchall()]

    conn.close()
    return jsonify({"status":"success", "new_balance": new_balance, "transactions": transactions})

@app.route('/get_wallet/<int:user_id>')
def get_wallet(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT wallet_balance FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    balance = row['wallet_balance'] if row else 0

    cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,))
    transactions = [dict(tx) for tx in cursor.fetchall()]
    conn.close()
    return jsonify({"balance": balance, "transactions": transactions})

# -----------------------------
# Orders & Automatic Commission
# -----------------------------
@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (customer_id, vendor_id, rider_id, product_amount, delivery_fee)
        VALUES (?, ?, ?, ?, ?)
    """, (data['customer_id'], data['vendor_id'], data['rider_id'], data['product_amount'], data['delivery_fee']))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return jsonify({"status":"success", "order_id": order_id})

@app.route('/process_payment/<int:order_id>', methods=['POST'])
def process_payment(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()
    if not order or order['status'] != 'pending':
        return jsonify({"status":"error", "message":"Order invalid or already processed"})

    # Amounts
    product_amount = order['product_amount']
    delivery_fee = order['delivery_fee']
    vendor_share = product_amount * 0.95
    rider_share = delivery_fee * 0.05
    platform_share = (product_amount + delivery_fee) - (vendor_share + rider_share)

    # Notification fees
    vendor_notification_fee = 50
    rider_notification_fee = 20

    # Update balances
    cursor.execute("UPDATE users SET wallet_balance=wallet_balance+? WHERE id=?",
                   (vendor_share - vendor_notification_fee, order['vendor_id']))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, category) VALUES (?,?,?,?)",
                   (order['vendor_id'], vendor_share - vendor_notification_fee, "credit", "vendor payment"))

    cursor.execute("UPDATE users SET wallet_balance=wallet_balance+? WHERE id=?",
                   (rider_share - rider_notification_fee, order['rider_id']))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, category) VALUES (?,?,?,?)",
                   (order['rider_id'], rider_share - rider_notification_fee, "credit", "rider payment"))

    # Platform earns commission + notification fees
    platform_total = platform_share + vendor_notification_fee + rider_notification_fee
    cursor.execute("UPDATE users SET wallet_balance=wallet_balance+? WHERE id=?", (platform_total, 0))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, category) VALUES (?,?,?,?)",
                   (0, platform_total, "credit", "platform commission + notifications"))

    # Mark order as paid
    cursor.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

    return jsonify({"status":"success","message":"Payment processed with commission and notification fees"})
    
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
