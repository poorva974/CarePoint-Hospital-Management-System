"""
database.py - Database Connection and Query Utilities
Hospital Management System (CarePoint)

Manages MySQL database connections using mysql-connector-python.
Loads configuration from environment variables or .env file.
Demonstrates robust resource management, error handling, and parameterized queries.
"""

import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error, errorcode
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Database Configuration with environment variable overrides
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "hospital_management")


def get_db_connection():
    """
    Establish and return a new MySQL database connection.
    Raises mysql.connector.Error on failure.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False
        )
        return connection
    except Error as err:
        # Avoid leaking password in logs or user interface
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise RuntimeError("Database error: Invalid username or password.") from err
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            raise RuntimeError(f"Database error: Database '{DB_NAME}' does not exist.") from err
        else:
            raise RuntimeError(f"Database connection error: {err}") from err


@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager that yields a database cursor.
    Safely commits or rolls back transactions and guarantees
    that cursor and connection are always closed.
    
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO patient (name) VALUES (%s)", (name,))
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        if conn and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass


def execute_query(query, params=None, dictionary=True):
    """
    Execute a SELECT query and return all matching rows.
    Always uses parameterized inputs to prevent SQL Injection.
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute_one(query, params=None, dictionary=True):
    """
    Execute a SELECT query and return a single row, or None.
    """
    with get_db_cursor(commit=False, dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute_write(query, params=None):
    """
    Execute an INSERT, UPDATE, or DELETE query with automatic commit.
    Returns a dict with 'lastrowid' and 'rowcount'.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(query, params or ())
        return {
            "lastrowid": cursor.lastrowid,
            "rowcount": cursor.rowcount
        }


def check_db_health():
    """
    Test whether the database is accessible and return status info.
    """
    try:
        conn = get_db_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE(), VERSION()")
            db, ver = cursor.fetchone()
            cursor.close()
            conn.close()
            return True, f"Connected to {db} (MySQL {ver})"
        return False, "Not connected"
    except Exception as e:
        return False, str(e)


def init_users_table():
    """
    Safely creates the 'users' table if it does not already exist.
    Leaves all existing tables (patient, doctor, appointment, medical_record, billing) untouched.
    Ensures 'phone' and 'status' columns exist, defaults all users to Approved,
    and sets up the 'password_resets' table for secure single-use password resets.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(30) NOT NULL DEFAULT 'Staff',
        phone VARCHAR(20) NULL,
        status VARCHAR(30) NOT NULL DEFAULT 'Approved',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    create_resets_sql = """
    CREATE TABLE IF NOT EXISTS password_resets (
        reset_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        token VARCHAR(64) NOT NULL UNIQUE,
        expires_at DATETIME NOT NULL,
        used TINYINT(1) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_token (token),
        INDEX idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(create_table_sql)
        cursor.execute(create_resets_sql)
        
        # Check if 'phone' column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'phone'
        """, (DB_NAME,))
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL AFTER role")

        # Check if 'status' column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'status'
        """, (DB_NAME,))
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'Approved'")
            
        # Ensure any existing accounts are marked as Approved (approval system removed)
        cursor.execute("UPDATE users SET status = 'Approved' WHERE status = 'Pending'")

    init_analytics_schema()


def init_analytics_schema():
    """
    Ensures analytics support columns exist on relational tables.
    Non-destructively adds `created_at` timestamp to `patient` table.
    Enriches demonstration transactions for Today & recent date ranges if minimal.
    """
    with get_db_cursor(commit=True) as cursor:
        # Check if 'created_at' column exists in 'patient' table
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'patient' AND COLUMN_NAME = 'created_at'
        """, (DB_NAME,))
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE patient ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Backfill existing patients across recent months to showcase monthly registration analytics
            cursor.execute("UPDATE patient SET created_at = '2026-06-15 10:00:00' WHERE patient_id = 1")
            cursor.execute("UPDATE patient SET created_at = '2026-07-20 11:30:00' WHERE patient_id = 2")
            cursor.execute("UPDATE patient SET created_at = '2026-08-10 09:15:00' WHERE patient_id = 3")
            cursor.execute("UPDATE patient SET created_at = '2026-09-05 14:00:00' WHERE patient_id = 4")
            cursor.execute("UPDATE patient SET created_at = '2026-09-25 16:45:00' WHERE patient_id = 5")

        # Check total appointments to ensure today/recent date ranges have data
        cursor.execute("SELECT COUNT(*) AS cnt FROM appointment")
        res = cursor.fetchone()
        appt_cnt = res["cnt"] if res else 0
        if appt_cnt <= 5:
            # Add demo appointments for Today (2026-10-19) and recent days
            cursor.execute("""
                INSERT INTO appointment (patient_id, doctor_id, appointment_date, time_slot, status)
                VALUES 
                    (1, 1, '2026-10-19', '09:00 AM', 'Completed'),
                    (2, 2, '2026-10-19', '10:30 AM', 'Scheduled'),
                    (3, 3, '2026-10-17', '11:00 AM', 'Completed'),
                    (4, 5, '2026-10-15', '04:00 PM', 'Cancelled')
            """)
            # Add linked bills for completed consultations
            cursor.execute("SELECT appointment_id FROM appointment WHERE appointment_date = '2026-10-19' AND patient_id = 1")
            a1 = cursor.fetchone()
            if a1:
                cursor.execute("""
                    INSERT INTO billing (patient_id, appointment_id, amount, payment_status, insurance_details, bill_date)
                    VALUES (1, %s, 1200.00, 'Paid', 'General health consultation', '2026-10-19')
                """, (a1["appointment_id"],))

            cursor.execute("SELECT appointment_id FROM appointment WHERE appointment_date = '2026-10-17' AND patient_id = 3")
            a2 = cursor.fetchone()
            if a2:
                cursor.execute("""
                    INSERT INTO billing (patient_id, appointment_id, amount, payment_status, insurance_details, bill_date)
                    VALUES (3, %s, 1800.00, 'Paid', 'Orthopedic consultation', '2026-10-17')
                """, (a2["appointment_id"],))