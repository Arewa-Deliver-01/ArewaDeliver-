import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
import sqlite3

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Initialize database
def init_db():
    conn = sqlite3.connect("deliveries.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pickup TEXT,
        delivery TEXT,
        package TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/request_delivery", methods=["POST"])
def request_delivery():
    data = request.json
    name = data.get("name")
    pickup = data.get("pickup")
    delivery = data.get("delivery")
    package = data.get("package")

    conn = sqlite3.connect("deliveries.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO deliveries (name, pickup, delivery, package) VALUES (?, ?, ?, ?)",
                   (name, pickup, delivery, package))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Delivery request stored successfully."})

@app.route("/api/ask", methods=["POST"])
def ask_ai():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"reply": "Please ask a question."})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are ArewaBot, a helpful delivery assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        reply = "Sorry, something went wrong with the AI."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
