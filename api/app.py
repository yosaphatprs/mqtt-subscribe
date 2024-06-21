from flask import Flask, request, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import connect, sql
import psycopg2.extras
from datetime import datetime, timedelta

app = Flask(__name__)

# PostgreSQL database connection settings
DB_NAME = "fall_detection"
DB_USER = "root"
DB_PASSWORD = "123"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')  # New addition for email

    if not username or not password or not email:
        return jsonify({"message": "Username, password, and email are required"}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = sql.SQL("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)")
        cursor.execute(insert_query, (username, hashed_password, email))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User registered successfully"}), 201
    except psycopg2.Error as e:
        return jsonify({"message": f"Failed to register user: {e}"}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            return jsonify({"message": "Login successful"}), 200
        else:
            return Response(
                "Could not verify", 401,
                {'WWW-Authenticate': 'Basic realm="Login required!"'}
            )
    except psycopg2.Error as e:
        return jsonify({"message": f"Failed to authenticate user: {e}"}), 500

@app.route('/fall_events', methods=['GET'])
def get_fall_events():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Calculate the date one month ago from today
        one_month_ago = datetime.now() - timedelta(days=30)

        # Query to get fall events from the last month
        cursor.execute("""
            SELECT * FROM fall_events 
            WHERE event_time >= %s
            ORDER BY event_time
        """, (one_month_ago,))

        fall_events = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert the result to a list of dictionaries
        fall_events_list = [dict(event) for event in fall_events]

        return jsonify(fall_events_list), 200
    except psycopg2.Error as e:
        return jsonify({"message": f"Failed to fetch fall events: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
