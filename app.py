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

    # Customers, vendors, riders all share similar profile structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,        -- customer, vendor, rider
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            profile_image TEXT DEFAULT 'default.png',
            wallet_balance REAL DEFAULT 0
        )
    """)

    # transactions table for wallets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,     -- credit or debit
            category TEXT, -- payment, delivery fee, commission, etc.
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

@app.route('/rider')
def rider_profile():
    return render_template("rider.html")

@app.route('/vendor')
def vendor_profile():
    return render_template("vendor.html")


# API FOR SAVING PROFILE DATA
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

if __name__ == "__main__":
    app.run(debug=True)
