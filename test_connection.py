import psycopg2

# PostgreSQL database connection settings
DB_NAME = "fall_detection"
DB_USER = "root"
DB_PASSWORD = "123"
DB_HOST = "localhost"
DB_PORT = "5432"

conn = None  # Initialize connection variable

try:
    # Establish connection to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("Connected to database successfully!")

    # Add your database operations here...

except psycopg2.Error as e:
    print(f"Failed to connect to the database: {e}")

finally:
    if conn is not None:
        conn.close()
        print("Database connection closed.")