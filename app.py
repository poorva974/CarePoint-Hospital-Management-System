"""
app.py - CarePoint Hospital Management System (HMS)
Full-Stack Flask Application demonstrating relational DBMS concepts.
Features:
- User Authentication & Route Protection (Landing, Login, Session Management, Logout)
- CRUD operations on 5 core relational tables (patient, doctor, appointment, medical_record, billing)
- Dedicated users table with secure password hashing (scrypt / Werkzeug)
- Referential integrity enforcement & safe foreign key checking
- Parameterized SQL queries preventing SQL Injection
- Multi-table INNER JOINs and LEFT JOINs
- Aggregate functions (COUNT, SUM, AVG) and GROUP BY analytics
- Session-based CSRF protection and server-side validation
- Post/Redirect/Get pattern with flash user feedback
"""

import os
import re
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session,
    jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from database import (
    get_db_connection,
    get_db_cursor,
    execute_query,
    execute_one,
    execute_write,
    check_db_health,
    init_users_table,
    DB_NAME
)

# Load environment configuration
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Guarantee users table exists
try:
    init_users_table()
except Exception as _e:
    pass


# --------------------------------------------------------------------------
# Security & CSRF Protection
# --------------------------------------------------------------------------
def generate_csrf_token():
    """Generate or retrieve a cryptographically secure CSRF token in the session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = generate_csrf_token


@app.before_request
def verify_csrf_protection():
    """
    Validate CSRF tokens for all state-changing HTTP methods.
    Exempts GET, HEAD, OPTIONS, and test environments.
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Allow internal testing flag if explicitly configured
        if app.config.get("WTF_CSRF_ENABLED") is False:
            return

        token = request.form.get("csrf_token")
        expected_token = session.get("csrf_token")

        if not expected_token or not token or token != expected_token:
            abort(400, description="Invalid or missing CSRF token. Please submit the form again.")


def login_required(f):
    """
    Decorator that enforces server-side route authentication.
    Redirects unauthenticated visitors to /login with target next URL.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access the hospital management dashboard.", "warning")
            target = request.full_path if request.query_string else request.path
            return redirect(url_for("login", next=target))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator that enforces Administrator privileges.
    Redirects unauthorized users to their dashboard with an alert.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access the requested resource.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") != "Administrator":
            flash("Access denied: Administrator privileges are required to access this section.", "danger")
            role = session.get("user_role")
            if role == "Patient":
                return redirect(url_for("patient_dashboard"))
            elif role == "Doctor":
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def staff_or_admin_required(f):
    """
    Decorator that enforces Staff or Administrator privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") not in ("Staff", "Administrator"):
            flash("Access restricted to hospital administrative staff.", "danger")
            role = session.get("user_role")
            if role == "Patient":
                return redirect(url_for("patient_dashboard"))
            elif role == "Doctor":
                return redirect(url_for("doctor_dashboard"))
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def doctor_staff_admin_required(f):
    """
    Decorator that enforces Doctor, Staff, or Administrator privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") not in ("Doctor", "Staff", "Administrator"):
            flash("Access restricted to hospital medical and operational personnel.", "danger")
            return redirect(url_for("patient_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_template_data():
    """Inject common variables into all Jinja2 templates."""
    today = date.today()
    return {
        "current_date": today.strftime("%d %b %Y"),
        "min_date": today.strftime("%Y-%m-%d"),
        "db_name": DB_NAME,
        "active_page": request.endpoint or "dashboard"
    }


# --------------------------------------------------------------------------
# Error Handlers
# --------------------------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return render_template("400.html", error_message=getattr(error, "description", None)), 400


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


# --------------------------------------------------------------------------
# Helper Validation Functions
# --------------------------------------------------------------------------
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
PHONE_REGEX = re.compile(r"^[0-9\+\-\s\(\)]{7,15}$")


def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email.strip())) if email else True


def is_valid_phone(phone):
    return bool(PHONE_REGEX.match(phone.strip())) if phone else True


def parse_date(date_str):
    """Safely parse YYYY-MM-DD date string, returning date object or None."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_decimal(val_str):
    """Safely parse numeric amount, returning Decimal or None."""
    if val_str is None or str(val_str).strip() == "":
        return None
    try:
        val = Decimal(str(val_str).strip())
        return val
    except (InvalidOperation, ValueError):
        return None


# ==========================================================================
# PUBLIC ROUTES: LANDING & AUTHENTICATION
# ==========================================================================
@app.route("/")
def landing():
    """Public promotional and overview landing page."""
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Public User Self-Registration Endpoint.
    Allows new users to register as Patient, Doctor, or Staff.
    Immediately creates active account with secure scrypt password hash.
    No administrator approval required.
    """
    if session.get("user_id"):
        role = session.get("user_role")
        if role == "Patient":
            return redirect(url_for("patient_dashboard"))
        elif role == "Doctor":
            return redirect(url_for("doctor_dashboard"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "Patient").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation 1: Required fields
        if not name or not email or not phone or not password or not confirm_password:
            flash("All fields marked with * are required. Please fill in all fields.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 2: Name length
        if len(name) < 2:
            flash("Full name must be at least 2 characters long.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 3: Email format
        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 4: Phone format
        if not PHONE_REGEX.match(phone):
            flash("Please enter a valid telephone or mobile number.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 5: Role security check (cannot select Administrator on public signup)
        if role not in ("Patient", "Doctor", "Staff"):
            flash("Invalid role selected. Allowed account roles are Patient, Doctor, or Staff.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role="Patient"), 400

        # Validation 6: Password length (at least 8 chars)
        if len(password) < 8:
            flash("Password must be at least 8 characters long for system security.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 7: Password confirmation match
        if password != confirm_password:
            flash("Password and confirmation password do not match. Please re-enter.", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 400

        # Validation 8: Duplicate email check
        existing = execute_one("SELECT user_id FROM users WHERE email = %s", (email,))
        if existing:
            flash("An account with this email address already exists. Please sign in or use another email.", "warning")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 409

        # Hash password securely using Werkzeug (scrypt)
        password_hash = generate_password_hash(password)

        try:
            # Insert user with status = 'Approved' (no admin approval needed)
            execute_write("""
                INSERT INTO users (name, email, phone, password_hash, role, status)
                VALUES (%s, %s, %s, %s, %s, 'Approved')
            """, (name, email, phone, password_hash, role))

            # Automatically link or seed profile in respective relational table
            if role == "Patient":
                pat = execute_one("SELECT patient_id FROM patient WHERE phone = %s OR name = %s", (phone, name))
                if not pat:
                    execute_write("""
                        INSERT INTO patient (name, gender, dob, phone, address)
                        VALUES (%s, 'Other', NULL, %s, 'Registered Online Portal')
                    """, (name, phone))
            elif role == "Doctor":
                doc = execute_one("SELECT doctor_id FROM doctor WHERE email = %s OR phone = %s", (email, phone))
                if not doc:
                    execute_write("""
                        INSERT INTO doctor (name, specialization, phone, email, department)
                        VALUES (%s, 'General Medicine', %s, %s, 'General Medicine')
                    """, (name, phone, email))

            flash(f"Account created successfully for {name}! You can now log in immediately with your credentials.", "success")
            return redirect(url_for("login", email=email))
        except Exception as e:
            flash(f"An error occurred while creating your account: {e}", "danger")
            return render_template("signup.html", name=name, email=email, phone=phone, role=role), 500

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User Authentication Endpoint.
    Validates credentials against MySQL users table using secure password hashing.
    Enables immediate login upon registration without administrator approval.
    Redirects to role-appropriate dashboard (Patient, Doctor, Staff, Administrator).
    """
    if session.get("user_id"):
        role = session.get("user_role")
        if role == "Patient":
            return redirect(url_for("patient_dashboard"))
        elif role == "Doctor":
            return redirect(url_for("doctor_dashboard"))
        return redirect(url_for("dashboard"))

    # Capture requested redirect target
    next_url = request.args.get("next") or request.form.get("next")
    # Sanitize next_url to prevent open redirect vulnerabilities
    if next_url and (not next_url.startswith("/") or next_url.startswith("//") or next_url.startswith("/login")):
        next_url = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember_me = bool(request.form.get("remember_me"))

        if not email or not password:
            flash("Please enter both your email address and password.", "danger")
            return render_template("login.html", next_url=next_url, submitted_email=email), 400

        # Query user record by email
        user = execute_one("SELECT * FROM users WHERE email = %s", (email,))

        # Verify password hash securely (constant-time, prevents user enumeration)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email address or password. Please verify your credentials.", "danger")
            return render_template("login.html", next_url=next_url, submitted_email=email), 401

        # Check if explicitly deactivated by administrator
        user_status = user.get("status", "Approved")
        if user_status == "Disabled":
            flash("Your account has been deactivated. Please contact your hospital administrator to restore access.", "danger")
            return render_template("login.html", next_url=next_url, submitted_email=email), 403

        # Clear and regenerate session to protect against session fixation attacks
        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        session["user_phone"] = user.get("phone")
        session["user_status"] = user_status
        if remember_me:
            session.permanent = True

        flash(f"Welcome back, {user['name']}! You have signed in successfully.", "success")

        # Determine target dashboard
        if next_url:
            return redirect(next_url)

        if user["role"] == "Patient":
            return redirect(url_for("patient_dashboard"))
        elif user["role"] == "Doctor":
            return redirect(url_for("doctor_dashboard"))
        else:
            return redirect(url_for("dashboard"))

    return render_template("login.html", next_url=next_url, submitted_email=request.args.get("email", ""))


@app.route("/logout")
def logout():
    """
    Log out of the application.
    Invalidates session and redirects to public landing page.
    """
    session.clear()
    flash("You have been signed out of CarePoint.", "info")
    return redirect(url_for("landing"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Secure password reset token generation.
    Creates an expiring, single-use reset token in the database.
    """
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Please enter your account email address.", "danger")
            return render_template("forgot_password.html"), 400

        user = execute_one("SELECT user_id, name, email FROM users WHERE email = %s", (email,))
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(minutes=15)
            # Invalidate any older unused tokens for this user
            execute_write("UPDATE password_resets SET used = 1 WHERE user_id = %s", (user["user_id"],))
            execute_write("""
                INSERT INTO password_resets (user_id, token, expires_at, used)
                VALUES (%s, %s, %s, 0)
            """, (user["user_id"], token, expires_at))

            reset_url = url_for("reset_password", token=token, _external=True)
            smtp_host = os.getenv("SMTP_HOST")
            if smtp_host:
                flash(f"A password reset link has been dispatched to {email}. Please check your inbox.", "info")
            else:
                # External SMTP not configured: explain configuration and show direct reset link for local testing
                flash(
                    f"Password reset link generated for <strong>{email}</strong>!<br>"
                    f"<span style='font-size:0.83rem;'>Note: External SMTP email service is not configured on this machine. "
                    f"To test password reset locally, use this link: "
                    f"<a href='{reset_url}' style='font-weight:700; color:#2563eb; text-decoration:underline;'>Reset Password Now</a></span>",
                    "info"
                )
            return render_template("forgot_password.html", submitted_email=email)
        else:
            flash("If an account exists for that email, a password reset link has been prepared.", "info")
            return render_template("forgot_password.html", submitted_email=email)

    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """
    Password reset fulfillment endpoint.
    Validates single-use token and expiration, updating user's password hash.
    """
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    token = request.args.get("token") or request.form.get("token")
    if not token:
        flash("Missing password reset token. Please request a new link.", "danger")
        return redirect(url_for("forgot_password"))

    reset_rec = execute_one("""
        SELECT r.*, u.email, u.name 
        FROM password_resets r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.token = %s AND r.used = 0
    """, (token,))

    if not reset_rec:
        flash("Invalid or already used password reset link. Please request a new one.", "danger")
        return redirect(url_for("forgot_password"))

    if reset_rec["expires_at"] < datetime.now():
        flash("This password reset link has expired. Please request a new one.", "warning")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            flash("Please fill in both password fields.", "danger")
            return render_template("reset_password.html", token=token, user_email=reset_rec["email"]), 400

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("reset_password.html", token=token, user_email=reset_rec["email"]), 400

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template("reset_password.html", token=token, user_email=reset_rec["email"]), 400

        new_hash = generate_password_hash(password)
        execute_write("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, reset_rec["user_id"]))
        execute_write("UPDATE password_resets SET used = 1 WHERE reset_id = %s", (reset_rec["reset_id"],))

        flash("Your password has been reset successfully! You can now log in with your new password.", "success")
        return redirect(url_for("login", email=reset_rec["email"]))

    return render_template("reset_password.html", token=token, user_email=reset_rec["email"])


# ==========================================================================
# 1. DASHBOARD MODULE (PROTECTED)
# ==========================================================================
@app.route("/dashboard")
@login_required
def dashboard():
    """
    Main Hospital Administration Dashboard (Staff & Administrator).
    Redirects Patients and Doctors to their respective dashboards.
    Demonstrates SQL aggregate queries (COUNT, SUM, AVG) and multi-table JOINs.
    """
    role = session.get("user_role")
    if role == "Patient":
        return redirect(url_for("patient_dashboard"))
    elif role == "Doctor":
        return redirect(url_for("doctor_dashboard"))

    # 1. Total Patients
    res_pat = execute_one("SELECT COUNT(*) AS total FROM patient")
    total_patients = res_pat["total"] if res_pat else 0

    # 2. Total Doctors
    res_doc = execute_one("SELECT COUNT(*) AS total FROM doctor")
    total_doctors = res_doc["total"] if res_doc else 0

    # 3. Total Appointments & Scheduled Count
    res_apt = execute_one("""
        SELECT 
            COUNT(*) AS total,
            COUNT(CASE WHEN status = 'Scheduled' THEN 1 END) AS scheduled
        FROM appointment
    """)
    total_appointments = res_apt["total"] if res_apt else 0
    scheduled_appointments = res_apt["scheduled"] if res_apt else 0

    # 4. Total Revenue from Paid Bills & Pending Amount
    res_rev = execute_one("""
        SELECT 
            COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END), 0) AS total_revenue,
            COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_revenue
        FROM billing
    """)
    total_revenue = res_rev["total_revenue"] if res_rev else Decimal("0.00")
    pending_revenue = res_rev["pending_revenue"] if res_rev else Decimal("0.00")

    # 5. Recent Appointments with SQL INNER JOINs
    recent_appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.doctor_id,
            d.name AS doctor_name,
            d.department,
            a.appointment_date,
            a.time_slot,
            a.status
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
        LIMIT 8
    """)

    # 6. Department Activity Analysis (GROUP BY Demo)
    department_stats = execute_query("""
        SELECT 
            COALESCE(d.department, 'General') AS department,
            COUNT(a.appointment_id) AS appt_count
        FROM doctor d
        LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
        GROUP BY d.department
        ORDER BY appt_count DESC
    """)

    # 7. Billing Status Breakdown (GROUP BY & SUM Demo)
    billing_stats = execute_query("""
        SELECT 
            payment_status,
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS total_amount
        FROM billing
        GROUP BY payment_status
        ORDER BY count DESC
    """)

    # 8. Recent Registered Patients (with created_at timestamp)
    recent_patients = execute_query("""
        SELECT 
            patient_id,
            name,
            gender,
            dob,
            phone,
            address,
            created_at
        FROM patient
        ORDER BY created_at DESC, patient_id DESC
        LIMIT 6
    """)

    stats = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "scheduled_appointments": scheduled_appointments,
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_appointments=recent_appointments,
        recent_patients=recent_patients,
        department_stats=department_stats,
        billing_stats=billing_stats
    )


@app.route("/api/dashboard/analytics")
@login_required
@staff_or_admin_required
def api_dashboard_analytics():
    """
    Dedicated Analytics API for Dashboard visual metrics, Chart.js graphs, and date filtering.
    Protected endpoint: Accessible only to Staff and Administrators.
    Calculates SQL aggregations for:
      - KPI summary metrics (patients, doctors, appointments, revenue)
      - Appointment Trends line chart
      - Appointment Status distribution doughnut chart
      - Monthly Patient Registrations bar chart
      - Appointments by Doctor bar chart
      - Department-wise Appointments bar chart
      - Revenue Overview line chart (Collected Paid vs Pending vs Total Billed)
      - Recent Appointments relational records
      - Recent Registered Patients
    """
    try:
        today = date.today()
        range_type = request.args.get("range", "this_month").lower().strip()
        custom_start_str = request.args.get("start_date", "").strip()
        custom_end_str = request.args.get("end_date", "").strip()

        # Determine date range boundaries
        if range_type == "today":
            start_date = today
            end_date = today
            range_label = f"Today ({today.strftime('%d %b %Y')})"
        elif range_type == "last_7_days":
            start_date = today - timedelta(days=6)
            end_date = today
            range_label = f"Last 7 Days ({start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')})"
        elif range_type == "last_30_days":
            start_date = today - timedelta(days=29)
            end_date = today
            range_label = f"Last 30 Days ({start_date.strftime('%d %b')} – {end_date.strftime('%d %b %Y')})"
        elif range_type == "this_month":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = date(today.year, 12, 31)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            range_label = f"This Month ({start_date.strftime('%B %Y')})"
        elif range_type == "custom":
            start_date = parse_date(custom_start_str) if custom_start_str else today.replace(day=1)
            end_date = parse_date(custom_end_str) if custom_end_str else today
            if start_date and end_date and start_date > end_date:
                start_date, end_date = end_date, start_date
            range_label = f"Custom Range ({start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')})"
        else:  # Fallback / all-time
            start_date = date(2020, 1, 1)
            end_date = date(2030, 12, 31)
            range_label = "All Records"

        # 1. Total Patients & Doctors (Global metrics)
        res_pat = execute_one("SELECT COUNT(*) AS total FROM patient")
        total_patients = res_pat["total"] if res_pat else 0

        res_doc = execute_one("SELECT COUNT(*) AS total FROM doctor")
        total_doctors = res_doc["total"] if res_doc else 0

        # 2. Appointments in Range
        res_apt = execute_one("""
            SELECT 
                COUNT(*) AS total,
                COUNT(CASE WHEN status = 'Scheduled' THEN 1 END) AS scheduled,
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) AS completed,
                COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS cancelled
            FROM appointment
            WHERE appointment_date BETWEEN %s AND %s
        """, (start_date, end_date))
        total_appointments_range = res_apt["total"] if res_apt else 0
        scheduled_appointments_range = res_apt["scheduled"] if res_apt else 0
        completed_appointments_range = res_apt["completed"] if res_apt else 0
        cancelled_appointments_range = res_apt["cancelled"] if res_apt else 0

        # Global appointments count
        res_all_apt = execute_one("SELECT COUNT(*) AS total FROM appointment")
        total_appointments_all = res_all_apt["total"] if res_all_apt else 0

        # 3. Revenue in Range (Paid collected vs Pending)
        res_rev = execute_one("""
            SELECT 
                COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END), 0) AS total_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_revenue,
                COALESCE(SUM(amount), 0) AS total_billed
            FROM billing
            WHERE bill_date BETWEEN %s AND %s
        """, (start_date, end_date))
        total_revenue = float(res_rev["total_revenue"]) if res_rev else 0.0
        pending_revenue = float(res_rev["pending_revenue"]) if res_rev else 0.0
        total_billed = float(res_rev["total_billed"]) if res_rev else 0.0

        # Global revenue collected
        res_all_rev = execute_one("""
            SELECT 
                COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END), 0) AS total_revenue,
                COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_revenue
            FROM billing
        """)
        all_time_revenue = float(res_all_rev["total_revenue"]) if res_all_rev else 0.0
        all_time_pending = float(res_all_rev["pending_revenue"]) if res_all_rev else 0.0

        # 4. Line Chart: Appointment Trends (Date vs Count)
        trend_rows = execute_query("""
            SELECT 
                appointment_date,
                DATE_FORMAT(appointment_date, '%%d %%b') AS date_label,
                COUNT(*) AS total_count,
                COUNT(CASE WHEN status = 'Scheduled' THEN 1 END) AS scheduled_count,
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) AS completed_count
            FROM appointment
            WHERE appointment_date BETWEEN %s AND %s
            GROUP BY appointment_date, date_label
            ORDER BY appointment_date ASC
        """, (start_date, end_date))

        appointment_trends = {
            "labels": [r["date_label"] for r in trend_rows],
            "total": [r["total_count"] for r in trend_rows],
            "scheduled": [r["scheduled_count"] for r in trend_rows],
            "completed": [r["completed_count"] for r in trend_rows]
        }

        # 5. Doughnut Chart: Appointment Status distribution (Counts & Percentages)
        status_rows = execute_query("""
            SELECT 
                status,
                COUNT(*) AS count
            FROM appointment
            WHERE appointment_date BETWEEN %s AND %s
            GROUP BY status
            ORDER BY count DESC
        """, (start_date, end_date))

        total_status_count = sum(r["count"] for r in status_rows)
        appointment_status = {
            "labels": [r["status"] for r in status_rows],
            "counts": [r["count"] for r in status_rows],
            "percentages": [round((r["count"] / total_status_count * 100), 1) if total_status_count > 0 else 0 for r in status_rows],
            "total": total_status_count
        }

        # 6. Bar Chart: Monthly Patient Registrations
        reg_rows = execute_query("""
            SELECT 
                DATE_FORMAT(created_at, '%%Y-%%m') AS month_key,
                DATE_FORMAT(created_at, '%%b %%Y') AS month_label,
                COUNT(*) AS count
            FROM patient
            WHERE created_at IS NOT NULL
            GROUP BY month_key, month_label
            ORDER BY month_key ASC
        """)
        patient_registrations = {
            "labels": [r["month_label"] for r in reg_rows],
            "counts": [r["count"] for r in reg_rows]
        }

        # 7. Bar Chart: Appointments by Doctor
        doc_rows = execute_query("""
            SELECT 
                d.doctor_id,
                d.name AS doctor_name,
                COALESCE(d.department, 'General') AS department,
                COUNT(a.appointment_id) AS count
            FROM doctor d
            LEFT JOIN appointment a ON d.doctor_id = a.doctor_id AND (a.appointment_date BETWEEN %s AND %s)
            GROUP BY d.doctor_id, d.name, d.department
            ORDER BY count DESC, d.name ASC
        """, (start_date, end_date))

        doctor_appointments = {
            "labels": [r["doctor_name"] for r in doc_rows],
            "counts": [r["count"] for r in doc_rows],
            "departments": [r["department"] for r in doc_rows]
        }

        # 8. Bar Chart: Department-wise Appointments
        dept_rows = execute_query("""
            SELECT 
                COALESCE(d.department, 'General') AS department,
                COUNT(a.appointment_id) AS count
            FROM doctor d
            INNER JOIN appointment a ON d.doctor_id = a.doctor_id
            WHERE a.appointment_date BETWEEN %s AND %s
            GROUP BY department
            ORDER BY count DESC
        """, (start_date, end_date))

        department_appointments = {
            "labels": [r["department"] for r in dept_rows],
            "counts": [r["count"] for r in dept_rows]
        }

        # 9. Line Chart: Revenue Overview (Dates vs Collected vs Pending)
        rev_trend_rows = execute_query("""
            SELECT 
                bill_date,
                DATE_FORMAT(bill_date, '%%d %%b') AS date_label,
                COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END), 0) AS collected,
                COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN amount ELSE 0 END), 0) AS pending,
                COALESCE(SUM(amount), 0) AS total
            FROM billing
            WHERE bill_date BETWEEN %s AND %s
            GROUP BY bill_date, date_label
            ORDER BY bill_date ASC
        """, (start_date, end_date))

        revenue_trends = {
            "labels": [r["date_label"] for r in rev_trend_rows],
            "collected": [float(r["collected"]) for r in rev_trend_rows],
            "pending": [float(r["pending"]) for r in rev_trend_rows],
            "total": [float(r["total"]) for r in rev_trend_rows]
        }

        # 10. Recent Appointments Table (Recent 8 joined records)
        recent_appointments = execute_query("""
            SELECT 
                a.appointment_id,
                a.patient_id,
                p.name AS patient_name,
                a.doctor_id,
                d.name AS doctor_name,
                d.department,
                a.appointment_date,
                DATE_FORMAT(a.appointment_date, '%%d %%b %%Y') AS formatted_date,
                a.time_slot,
                a.status
            FROM appointment a
            INNER JOIN patient p ON a.patient_id = p.patient_id
            INNER JOIN doctor d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC, a.appointment_id DESC
            LIMIT 8
        """)
        for a in recent_appointments:
            if isinstance(a.get("appointment_date"), (date, datetime)):
                a["appointment_date"] = a["appointment_date"].strftime("%Y-%m-%d")

        # 11. Recent Patients Section
        recent_patients = execute_query("""
            SELECT 
                patient_id,
                name,
                gender,
                dob,
                DATE_FORMAT(dob, '%%d %%b %%Y') AS formatted_dob,
                phone,
                address,
                created_at,
                DATE_FORMAT(created_at, '%%d %%b %%Y') AS formatted_created_at
            FROM patient
            ORDER BY created_at DESC, patient_id DESC
            LIMIT 6
        """)
        for p in recent_patients:
            if isinstance(p.get("dob"), (date, datetime)):
                p["dob"] = p["dob"].strftime("%Y-%m-%d")
            if isinstance(p.get("created_at"), (date, datetime)):
                p["created_at"] = p["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        payload = {
            "success": True,
            "range": {
                "type": range_type,
                "label": range_label,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "stats": {
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "total_appointments": total_appointments_range,
                "scheduled_appointments": scheduled_appointments_range,
                "completed_appointments": completed_appointments_range,
                "cancelled_appointments": cancelled_appointments_range,
                "all_time_appointments": total_appointments_all,
                "total_revenue": total_revenue,
                "pending_revenue": pending_revenue,
                "total_billed": total_billed,
                "all_time_revenue": all_time_revenue,
                "all_time_pending": all_time_pending
            },
            "appointment_trends": appointment_trends,
            "appointment_status": appointment_status,
            "patient_registrations": patient_registrations,
            "doctor_appointments": doctor_appointments,
            "department_appointments": department_appointments,
            "revenue_trends": revenue_trends,
            "recent_appointments": recent_appointments,
            "recent_patients": recent_patients
        }
        return jsonify(payload)

    except Exception as e:
        app.logger.error(f"Error in api_dashboard_analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to calculate analytics metrics. Please verify database connectivity.",
            "details": str(e)
        }), 500


@app.route("/dashboard/patient")
@login_required
def patient_dashboard():
    """
    Patient-Specific Healthcare Portal.
    Displays patient's personal appointment history, clinical notes, and billing receipts.
    """
    user_phone = session.get("user_phone")
    user_name = session.get("user_name")
    user_email = session.get("user_email")

    patient_rec = None
    if user_phone:
        patient_rec = execute_one("SELECT * FROM patient WHERE phone = %s", (user_phone,))
    if not patient_rec and user_name:
        patient_rec = execute_one("SELECT * FROM patient WHERE name = %s", (user_name,))

    patient_id = patient_rec["patient_id"] if patient_rec else None

    appointments = []
    medical_records = []
    bills = []
    upcoming_count = 0

    if patient_id:
        appointments = execute_query("""
            SELECT a.*, d.name AS doctor_name, d.department
            FROM appointment a
            JOIN doctor d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.time_slot DESC
        """, (patient_id,))
        upcoming_count = sum(1 for a in appointments if a.get("status") == "Scheduled")

        medical_records = execute_query("""
            SELECT m.*, d.name AS doctor_name
            FROM medical_record m
            JOIN doctor d ON m.doctor_id = d.doctor_id
            WHERE m.patient_id = %s
            ORDER BY m.record_date DESC, m.record_id DESC
        """, (patient_id,))

        bills = execute_query("""
            SELECT * FROM billing
            WHERE patient_id = %s
            ORDER BY bill_date DESC, bill_id DESC
        """, (patient_id,))

    return render_template(
        "dashboard_patient.html",
        patient=patient_rec,
        appointments=appointments,
        upcoming_count=upcoming_count,
        medical_records=medical_records,
        bills=bills,
        active_page="patient_dashboard"
    )


@app.route("/dashboard/doctor")
@login_required
def doctor_dashboard():
    """
    Doctor-Specific Consultation Portal.
    Displays attending physician's scheduled appointments and authored clinical charts.
    """
    if session.get("user_role") not in ("Doctor", "Administrator", "Staff"):
        flash("Access restricted to medical personnel.", "danger")
        return redirect(url_for("patient_dashboard"))

    user_email = session.get("user_email")
    user_phone = session.get("user_phone")
    user_name = session.get("user_name")

    doc_rec = None
    if user_email:
        doc_rec = execute_one("SELECT * FROM doctor WHERE email = %s", (user_email,))
    if not doc_rec and user_phone:
        doc_rec = execute_one("SELECT * FROM doctor WHERE phone = %s", (user_phone,))
    if not doc_rec and user_name:
        doc_rec = execute_one("SELECT * FROM doctor WHERE name = %s OR name LIKE %s", (user_name, f"%{user_name}%"))

    doctor_id = doc_rec["doctor_id"] if doc_rec else None

    appointments = []
    medical_records = []
    scheduled_count = 0
    patient_count = 0

    if doctor_id:
        appointments = execute_query("""
            SELECT a.*, p.name AS patient_name, p.phone AS patient_phone
            FROM appointment a
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date DESC, a.time_slot DESC
        """, (doctor_id,))
        scheduled_count = sum(1 for a in appointments if a.get("status") == "Scheduled")
        patient_ids = set(a["patient_id"] for a in appointments)
        patient_count = len(patient_ids)

        medical_records = execute_query("""
            SELECT m.*, p.name AS patient_name
            FROM medical_record m
            JOIN patient p ON m.patient_id = p.patient_id
            WHERE m.doctor_id = %s
            ORDER BY m.record_date DESC, m.record_id DESC
        """, (doctor_id,))
    else:
        appointments = execute_query("""
            SELECT a.*, p.name AS patient_name, p.phone AS patient_phone
            FROM appointment a
            JOIN patient p ON a.patient_id = p.patient_id
            ORDER BY a.appointment_date DESC, a.time_slot DESC
            LIMIT 10
        """)
        scheduled_count = sum(1 for a in appointments if a.get("status") == "Scheduled")

    return render_template(
        "dashboard_doctor.html",
        doctor_info=doc_rec,
        appointments=appointments,
        scheduled_count=scheduled_count,
        medical_records=medical_records,
        patient_count=patient_count,
        active_page="doctor_dashboard"
    )


# ==========================================================================
# 2. PATIENT MANAGEMENT MODULE (PROTECTED)
# ==========================================================================
@app.route("/patients")
@login_required
def patients_list():
    """Display all patients with optional search by name or phone."""
    search_query = request.args.get("q", "").strip()

    if search_query:
        query = """
            SELECT * FROM patient
            WHERE name LIKE %s OR phone LIKE %s
            ORDER BY patient_id DESC
        """
        wildcard = f"%{search_query}%"
        patients = execute_query(query, (wildcard, wildcard))
    else:
        patients = execute_query("SELECT * FROM patient ORDER BY patient_id DESC")

    return render_template(
        "patients.html",
        patients=patients,
        search_query=search_query
    )


@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    """View full profile of a patient including appointment and billing history."""
    patient = execute_one("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
    if not patient:
        flash("Patient record not found.", "warning")
        return redirect(url_for("patients_list"))

    # Related appointments via INNER JOIN
    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.time_slot,
            a.status,
            d.doctor_id,
            d.name AS doctor_name,
            d.department
        FROM appointment a
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """, (patient_id,))

    # Related medical records via INNER JOIN
    medical_records = execute_query("""
        SELECT 
            m.record_id,
            m.record_date,
            m.diagnosis,
            m.prescription,
            m.report,
            d.name AS doctor_name
        FROM medical_record m
        INNER JOIN doctor d ON m.doctor_id = d.doctor_id
        WHERE m.patient_id = %s
        ORDER BY m.record_date DESC, m.record_id DESC
    """, (patient_id,))

    # Related bills
    bills = execute_query("""
        SELECT * FROM billing
        WHERE patient_id = %s
        ORDER BY bill_date DESC, bill_id DESC
    """, (patient_id,))

    return render_template(
        "patient_detail.html",
        patient=patient,
        appointments=appointments,
        medical_records=medical_records,
        bills=bills
    )


@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def patient_add():
    """Register a new patient into the database."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip() or None
        dob_raw = request.form.get("dob", "").strip()
        phone = request.form.get("phone", "").strip() or None
        address = request.form.get("address", "").strip() or None

        # Server-side validation
        if not name:
            flash("Patient full name is required.", "danger")
            return render_template("patient_form.html", form_data=request.form), 400

        dob = parse_date(dob_raw)
        if dob_raw and not dob:
            flash("Invalid date of birth format.", "danger")
            return render_template("patient_form.html", form_data=request.form), 400

        if dob and dob > date.today():
            flash("Date of birth cannot be in the future.", "danger")
            return render_template("patient_form.html", form_data=request.form), 400

        if phone and not is_valid_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template("patient_form.html", form_data=request.form), 400

        try:
            execute_write("""
                INSERT INTO patient (name, gender, dob, phone, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, gender, dob, phone, address))
            flash(f"Patient '{name}' successfully registered!", "success")
            return redirect(url_for("patients_list"))
        except Exception as e:
            flash(f"Database error while saving patient: {e}", "danger")
            return render_template("patient_form.html", form_data=request.form), 500

    return render_template("patient_form.html", patient=None)


@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def patient_edit(patient_id):
    """Edit existing patient demographic information."""
    patient = execute_one("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
    if not patient:
        flash("Patient not found.", "warning")
        return redirect(url_for("patients_list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip() or None
        dob_raw = request.form.get("dob", "").strip()
        phone = request.form.get("phone", "").strip() or None
        address = request.form.get("address", "").strip() or None

        if not name:
            flash("Patient name is required.", "danger")
            return render_template("patient_form.html", patient=patient, form_data=request.form), 400

        dob = parse_date(dob_raw)
        if dob_raw and not dob:
            flash("Invalid date of birth.", "danger")
            return render_template("patient_form.html", patient=patient, form_data=request.form), 400

        if dob and dob > date.today():
            flash("Date of birth cannot be in the future.", "danger")
            return render_template("patient_form.html", patient=patient, form_data=request.form), 400

        if phone and not is_valid_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template("patient_form.html", patient=patient, form_data=request.form), 400

        try:
            execute_write("""
                UPDATE patient
                SET name = %s, gender = %s, dob = %s, phone = %s, address = %s
                WHERE patient_id = %s
            """, (name, gender, dob, phone, address, patient_id))
            flash(f"Patient '{name}' details updated successfully.", "success")
            return redirect(url_for("patient_detail", patient_id=patient_id))
        except Exception as e:
            flash(f"Error updating patient: {e}", "danger")
            return render_template("patient_form.html", patient=patient, form_data=request.form), 500

    return render_template("patient_form.html", patient=patient)


@app.route("/patients/<int:patient_id>/delete", methods=["POST"])
@login_required
def patient_delete(patient_id):
    """
    Safely delete a patient only if no foreign key constraints are violated.
    Prevents silent cascading data loss.
    """
    patient = execute_one("SELECT * FROM patient WHERE patient_id = %s", (patient_id,))
    if not patient:
        flash("Patient does not exist.", "warning")
        return redirect(url_for("patients_list"))

    # Check dependent records across all 3 child tables
    apt_cnt = execute_one("SELECT COUNT(*) AS cnt FROM appointment WHERE patient_id = %s", (patient_id,))["cnt"]
    med_cnt = execute_one("SELECT COUNT(*) AS cnt FROM medical_record WHERE patient_id = %s", (patient_id,))["cnt"]
    bil_cnt = execute_one("SELECT COUNT(*) AS cnt FROM billing WHERE patient_id = %s", (patient_id,))["cnt"]

    if apt_cnt > 0 or med_cnt > 0 or bil_cnt > 0:
        flash(
            f"Referential Integrity Alert: Cannot delete Patient '{patient['name']}' (ID: #{patient_id}) "
            f"because they have {apt_cnt} appointment(s), {med_cnt} medical record(s), and {bil_cnt} bill(s) associated with them. "
            "To preserve clinical audit trails, dependent records must first be deleted or cancelled.",
            "warning"
        )
        return redirect(url_for("patient_detail", patient_id=patient_id))

    try:
        execute_write("DELETE FROM patient WHERE patient_id = %s", (patient_id,))
        flash(f"Patient '{patient['name']}' was safely deleted.", "success")
    except Exception as e:
        flash(f"Deletion failed due to foreign key constraint: {e}", "danger")

    return redirect(url_for("patients_list"))


# ==========================================================================
# 3. DOCTOR MANAGEMENT MODULE (PROTECTED)
# ==========================================================================
@app.route("/doctors")
@login_required
def doctors_list():
    """Display all doctors with search and appointment count."""
    search_query = request.args.get("q", "").strip()

    if search_query:
        query = """
            SELECT 
                d.*,
                COUNT(a.appointment_id) AS appt_count
            FROM doctor d
            LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
            WHERE d.name LIKE %s OR d.specialization LIKE %s OR d.department LIKE %s
            GROUP BY d.doctor_id
            ORDER BY d.doctor_id DESC
        """
        wildcard = f"%{search_query}%"
        doctors = execute_query(query, (wildcard, wildcard, wildcard))
    else:
        doctors = execute_query("""
            SELECT 
                d.*,
                COUNT(a.appointment_id) AS appt_count
            FROM doctor d
            LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
            GROUP BY d.doctor_id
            ORDER BY d.doctor_id DESC
        """)

    return render_template(
        "doctors.html",
        doctors=doctors,
        search_query=search_query
    )


@app.route("/doctors/<int:doctor_id>")
@login_required
def doctor_detail(doctor_id):
    """View doctor profile and assigned appointments."""
    doctor = execute_one("SELECT * FROM doctor WHERE doctor_id = %s", (doctor_id,))
    if not doctor:
        flash("Doctor record not found.", "warning")
        return redirect(url_for("doctors_list"))

    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.appointment_date,
            a.time_slot,
            a.status
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        WHERE a.doctor_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """, (doctor_id,))

    return render_template(
        "doctor_detail.html",
        doctor=doctor,
        appointments=appointments
    )


@app.route("/doctors/add", methods=["GET", "POST"])
@login_required
def doctor_add():
    """Register a new doctor."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        specialization = request.form.get("specialization", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        email = request.form.get("email", "").strip() or None
        department = request.form.get("department", "").strip() or None

        if not name:
            flash("Doctor name is required.", "danger")
            return render_template("doctor_form.html", form_data=request.form), 400

        if email and not is_valid_email(email):
            flash("Invalid email address format.", "danger")
            return render_template("doctor_form.html", form_data=request.form), 400

        if phone and not is_valid_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template("doctor_form.html", form_data=request.form), 400

        try:
            execute_write("""
                INSERT INTO doctor (name, specialization, phone, email, department)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, specialization, phone, email, department))
            flash(f"Doctor '{name}' added successfully!", "success")
            return redirect(url_for("doctors_list"))
        except Exception as e:
            flash(f"Error adding doctor: {e}", "danger")
            return render_template("doctor_form.html", form_data=request.form), 500

    return render_template("doctor_form.html", doctor=None)


@app.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@login_required
def doctor_edit(doctor_id):
    """Edit existing doctor information."""
    doctor = execute_one("SELECT * FROM doctor WHERE doctor_id = %s", (doctor_id,))
    if not doctor:
        flash("Doctor not found.", "warning")
        return redirect(url_for("doctors_list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        specialization = request.form.get("specialization", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        email = request.form.get("email", "").strip() or None
        department = request.form.get("department", "").strip() or None

        if not name:
            flash("Doctor name is required.", "danger")
            return render_template("doctor_form.html", doctor=doctor, form_data=request.form), 400

        if email and not is_valid_email(email):
            flash("Invalid email address format.", "danger")
            return render_template("doctor_form.html", doctor=doctor, form_data=request.form), 400

        if phone and not is_valid_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template("doctor_form.html", doctor=doctor, form_data=request.form), 400

        try:
            execute_write("""
                UPDATE doctor
                SET name = %s, specialization = %s, phone = %s, email = %s, department = %s
                WHERE doctor_id = %s
            """, (name, specialization, phone, email, department, doctor_id))
            flash(f"Doctor '{name}' profile updated.", "success")
            return redirect(url_for("doctor_detail", doctor_id=doctor_id))
        except Exception as e:
            flash(f"Error updating doctor: {e}", "danger")
            return render_template("doctor_form.html", doctor=doctor, form_data=request.form), 500

    return render_template("doctor_form.html", doctor=doctor)


@app.route("/doctors/<int:doctor_id>/delete", methods=["POST"])
@login_required
def doctor_delete(doctor_id):
    """Safely delete a doctor only when foreign key constraints allow it."""
    doctor = execute_one("SELECT * FROM doctor WHERE doctor_id = %s", (doctor_id,))
    if not doctor:
        flash("Doctor not found.", "warning")
        return redirect(url_for("doctors_list"))

    apt_cnt = execute_one("SELECT COUNT(*) AS cnt FROM appointment WHERE doctor_id = %s", (doctor_id,))["cnt"]
    med_cnt = execute_one("SELECT COUNT(*) AS cnt FROM medical_record WHERE doctor_id = %s", (doctor_id,))["cnt"]

    if apt_cnt > 0 or med_cnt > 0:
        flash(
            f"Referential Integrity Alert: Cannot delete Doctor '{doctor['name']}' (ID: #{doctor_id}) "
            f"because {apt_cnt} appointment(s) and {med_cnt} medical record(s) reference them. "
            "Reassign or delete these records before removing the doctor.",
            "warning"
        )
        return redirect(url_for("doctor_detail", doctor_id=doctor_id))

    try:
        execute_write("DELETE FROM doctor WHERE doctor_id = %s", (doctor_id,))
        flash(f"Doctor '{doctor['name']}' removed from database.", "success")
    except Exception as e:
        flash(f"Deletion failed: {e}", "danger")

    return redirect(url_for("doctors_list"))


# ==========================================================================
# 4. APPOINTMENT MANAGEMENT MODULE (PROTECTED)
# ==========================================================================
@app.route("/appointments")
@login_required
def appointments_list():
    """Display appointments with multi-criteria search and filters."""
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    doctor_id = request.args.get("doctor_id", "").strip()
    date_val = request.args.get("date", "").strip()

    sql = """
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            p.phone AS patient_phone,
            a.doctor_id,
            d.name AS doctor_name,
            d.department,
            a.appointment_date,
            a.time_slot,
            a.status
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (p.name LIKE %s OR d.name LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if status:
        sql += " AND a.status = %s"
        params.append(status)
    if doctor_id:
        sql += " AND a.doctor_id = %s"
        params.append(doctor_id)
    if date_val:
        sql += " AND a.appointment_date = %s"
        params.append(date_val)

    sql += " ORDER BY a.appointment_date DESC, a.appointment_id DESC"
    appointments = execute_query(sql, params)

    doctors = execute_query("SELECT doctor_id, name FROM doctor ORDER BY name ASC")

    filters = {
        "q": q,
        "status": status,
        "doctor_id": doctor_id,
        "date": date_val
    }

    return render_template(
        "appointments.html",
        appointments=appointments,
        doctors=doctors,
        filters=filters
    )


@app.route("/appointments/<int:appointment_id>")
@login_required
def appointment_detail(appointment_id):
    """View appointment details along with linked clinical notes and invoice."""
    appointment = execute_one("""
        SELECT 
            a.*,
            p.name AS patient_name,
            p.phone AS patient_phone,
            d.name AS doctor_name,
            d.specialization AS doctor_specialization,
            d.department
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        WHERE a.appointment_id = %s
    """, (appointment_id,))

    if not appointment:
        flash("Appointment not found.", "warning")
        return redirect(url_for("appointments_list"))

    # Linked clinical medical record
    medical_record = execute_one("""
        SELECT * FROM medical_record WHERE appointment_id = %s
    """, (appointment_id,))

    # Linked bill
    bill = execute_one("""
        SELECT * FROM billing WHERE appointment_id = %s
    """, (appointment_id,))

    return render_template(
        "appointment_detail.html",
        appointment=appointment,
        medical_record=medical_record,
        bill=bill
    )


@app.route("/appointments/add", methods=["GET", "POST"])
@login_required
def appointment_add():
    """
    Book a new appointment.
    Validates patient & doctor existence, prevents past bookings,
    and checks for doctor scheduling conflicts.
    """
    patients = execute_query("SELECT patient_id, name, phone FROM patient ORDER BY name ASC")
    doctors = execute_query("SELECT doctor_id, name, specialization, department FROM doctor ORDER BY name ASC")

    preselect_patient_id = request.args.get("patient_id")
    preselect_doctor_id = request.args.get("doctor_id")

    if session.get("user_role") == "Patient" and not preselect_patient_id:
        user_phone = session.get("user_phone")
        user_name = session.get("user_name")
        pat = None
        if user_phone:
            pat = execute_one("SELECT patient_id FROM patient WHERE phone = %s", (user_phone,))
        if not pat and user_name:
            pat = execute_one("SELECT patient_id FROM patient WHERE name = %s", (user_name,))
        if pat:
            preselect_patient_id = pat["patient_id"]

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appt_date_raw = request.form.get("appointment_date", "").strip()
        time_slot = request.form.get("time_slot", "").strip()
        status = request.form.get("status", "Scheduled").strip()

        # Validation
        if not patient_id or not doctor_id or not appt_date_raw or not time_slot:
            flash("All appointment fields marked with * are required.", "danger")
            return render_template(
                "appointment_form.html",
                patients=patients,
                doctors=doctors,
                form_data=request.form
            ), 400

        appt_date = parse_date(appt_date_raw)
        if not appt_date:
            flash("Invalid appointment date format.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 400

        # Prevent past appointments
        if appt_date < date.today():
            flash("Invalid date: Cannot schedule appointments in the past.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 400

        # Verify patient and doctor exist
        if not execute_one("SELECT patient_id FROM patient WHERE patient_id = %s", (patient_id,)):
            flash("Selected patient does not exist in the database.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 400

        doctor = execute_one("SELECT name FROM doctor WHERE doctor_id = %s", (doctor_id,))
        if not doctor:
            flash("Selected doctor does not exist in the database.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 400

        # Prevent conflicting appointments for the same doctor and time slot (excluding cancelled)
        conflict = execute_one("""
            SELECT COUNT(*) AS cnt 
            FROM appointment 
            WHERE doctor_id = %s AND appointment_date = %s AND time_slot = %s AND status != 'Cancelled'
        """, (doctor_id, appt_date, time_slot))

        if conflict and conflict["cnt"] > 0:
            flash(
                f"Scheduling Conflict: {doctor['name']} already has an active appointment scheduled on {appt_date} at {time_slot}. "
                "Please choose an alternate time slot or doctor.",
                "warning"
            )
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 400

        # Database Transaction write
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO appointment (patient_id, doctor_id, appointment_date, time_slot, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (patient_id, doctor_id, appt_date, time_slot, status))
            flash(f"Appointment scheduled successfully for {appt_date} at {time_slot}!", "success")
            if session.get("user_role") == "Patient":
                return redirect(url_for("patient_dashboard"))
            return redirect(url_for("appointments_list"))
        except Exception as e:
            flash(f"Error booking appointment: {e}", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form_data=request.form), 500

    return render_template(
        "appointment_form.html",
        appointment=None,
        patients=patients,
        doctors=doctors,
        preselect_patient_id=preselect_patient_id,
        preselect_doctor_id=preselect_doctor_id
    )


@app.route("/appointments/<int:appointment_id>/edit", methods=["GET", "POST"])
@login_required
def appointment_edit(appointment_id):
    """Edit or reschedule an appointment."""
    appointment = execute_one("SELECT * FROM appointment WHERE appointment_id = %s", (appointment_id,))
    if not appointment:
        flash("Appointment not found.", "warning")
        return redirect(url_for("appointments_list"))

    patients = execute_query("SELECT patient_id, name, phone FROM patient ORDER BY name ASC")
    doctors = execute_query("SELECT doctor_id, name, specialization, department FROM doctor ORDER BY name ASC")

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appt_date_raw = request.form.get("appointment_date", "").strip()
        time_slot = request.form.get("time_slot", "").strip()
        status = request.form.get("status", "Scheduled").strip()

        if not patient_id or not doctor_id or not appt_date_raw or not time_slot:
            flash("All appointment fields marked with * are required.", "danger")
            return render_template("appointment_form.html", appointment=appointment, patients=patients, doctors=doctors, form_data=request.form), 400

        appt_date = parse_date(appt_date_raw)
        if not appt_date:
            flash("Invalid date format.", "danger")
            return render_template("appointment_form.html", appointment=appointment, patients=patients, doctors=doctors, form_data=request.form), 400

        # Conflict check excluding this appointment
        conflict = execute_one("""
            SELECT COUNT(*) AS cnt 
            FROM appointment 
            WHERE doctor_id = %s AND appointment_date = %s AND time_slot = %s AND status != 'Cancelled' AND appointment_id != %s
        """, (doctor_id, appt_date, time_slot, appointment_id))

        if conflict and conflict["cnt"] > 0:
            flash(f"Scheduling Conflict: The doctor is already booked for {appt_date} at {time_slot}.", "warning")
            return render_template("appointment_form.html", appointment=appointment, patients=patients, doctors=doctors, form_data=request.form), 400

        try:
            execute_write("""
                UPDATE appointment
                SET patient_id = %s, doctor_id = %s, appointment_date = %s, time_slot = %s, status = %s
                WHERE appointment_id = %s
            """, (patient_id, doctor_id, appt_date, time_slot, status, appointment_id))
            flash("Appointment updated successfully.", "success")
            return redirect(url_for("appointment_detail", appointment_id=appointment_id))
        except Exception as e:
            flash(f"Error updating appointment: {e}", "danger")
            return render_template("appointment_form.html", appointment=appointment, patients=patients, doctors=doctors, form_data=request.form), 500

    return render_template(
        "appointment_form.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors
    )


@app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@login_required
def appointment_status_update(appointment_id):
    """Quickly update appointment status (e.g., Mark Completed or Cancel)."""
    new_status = request.form.get("status", "").strip()
    if new_status not in ("Scheduled", "Completed", "Cancelled"):
        flash("Invalid status selected.", "danger")
        return redirect(url_for("appointment_detail", appointment_id=appointment_id))

    execute_write("UPDATE appointment SET status = %s WHERE appointment_id = %s", (new_status, appointment_id))
    flash(f"Appointment #{appointment_id} status changed to {new_status}.", "success")
    return redirect(url_for("appointment_detail", appointment_id=appointment_id))


@app.route("/appointments/<int:appointment_id>/delete", methods=["POST"])
@login_required
def appointment_delete(appointment_id):
    """Safely delete appointment with foreign key protection."""
    appt = execute_one("SELECT * FROM appointment WHERE appointment_id = %s", (appointment_id,))
    if not appt:
        flash("Appointment not found.", "warning")
        return redirect(url_for("appointments_list"))

    med_cnt = execute_one("SELECT COUNT(*) AS cnt FROM medical_record WHERE appointment_id = %s", (appointment_id,))["cnt"]
    bil_cnt = execute_one("SELECT COUNT(*) AS cnt FROM billing WHERE appointment_id = %s", (appointment_id,))["cnt"]

    if med_cnt > 0 or bil_cnt > 0:
        flash(
            f"Referential Integrity Alert: Cannot delete Appointment #{appointment_id} because "
            f"{med_cnt} medical record(s) and {bil_cnt} billing invoice(s) reference it. "
            "Please cancel the appointment instead of deleting it, or delete the dependent records first.",
            "warning"
        )
        return redirect(url_for("appointment_detail", appointment_id=appointment_id))

    try:
        execute_write("DELETE FROM appointment WHERE appointment_id = %s", (appointment_id,))
        flash(f"Appointment #{appointment_id} was deleted successfully.", "success")
    except Exception as e:
        flash(f"Could not delete appointment: {e}", "danger")

    return redirect(url_for("appointments_list"))


# ==========================================================================
# 5. MEDICAL RECORDS MODULE (PROTECTED)
# ==========================================================================
@app.route("/medical-records")
@login_required
def medical_records_list():
    """Display medical records with multi-table JOINs, search and filters."""
    q = request.args.get("q", "").strip()
    doctor_id = request.args.get("doctor_id", "").strip()
    date_val = request.args.get("date", "").strip()

    sql = """
        SELECT 
            m.record_id,
            m.patient_id,
            p.name AS patient_name,
            m.doctor_id,
            d.name AS doctor_name,
            m.appointment_id,
            a.appointment_date,
            m.diagnosis,
            m.prescription,
            m.report,
            m.record_date
        FROM medical_record m
        INNER JOIN patient p ON m.patient_id = p.patient_id
        INNER JOIN doctor d ON m.doctor_id = d.doctor_id
        INNER JOIN appointment a ON m.appointment_id = a.appointment_id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (p.name LIKE %s OR m.diagnosis LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if doctor_id:
        sql += " AND m.doctor_id = %s"
        params.append(doctor_id)
    if date_val:
        sql += " AND m.record_date = %s"
        params.append(date_val)

    sql += " ORDER BY m.record_date DESC, m.record_id DESC"
    records = execute_query(sql, params)

    doctors = execute_query("SELECT doctor_id, name FROM doctor ORDER BY name ASC")

    filters = {"q": q, "doctor_id": doctor_id, "date": date_val}

    return render_template(
        "medical_records.html",
        records=records,
        doctors=doctors,
        filters=filters
    )


@app.route("/medical-records/<int:record_id>")
@login_required
def medical_record_detail(record_id):
    """View detailed clinical record."""
    record = execute_one("""
        SELECT 
            m.*,
            p.name AS patient_name,
            d.name AS doctor_name,
            d.specialization AS doctor_specialization,
            d.department,
            a.appointment_date
        FROM medical_record m
        INNER JOIN patient p ON m.patient_id = p.patient_id
        INNER JOIN doctor d ON m.doctor_id = d.doctor_id
        INNER JOIN appointment a ON m.appointment_id = a.appointment_id
        WHERE m.record_id = %s
    """, (record_id,))

    if not record:
        flash("Medical record not found.", "warning")
        return redirect(url_for("medical_records_list"))

    return render_template("medical_record_detail.html", record=record)


@app.route("/medical-records/add", methods=["GET", "POST"])
@login_required
def medical_record_add():
    """
    Create a new medical record.
    Enforces referential consistency: appointment MUST belong to the selected patient and doctor.
    """
    patients = execute_query("SELECT patient_id, name FROM patient ORDER BY name ASC")
    doctors = execute_query("SELECT doctor_id, name, specialization FROM doctor ORDER BY name ASC")
    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.doctor_id,
            d.name AS doctor_name,
            a.appointment_date
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """)

    preselect_appointment_id = request.args.get("appointment_id")
    preselect_patient_id = request.args.get("patient_id")
    preselect_doctor_id = None

    if preselect_appointment_id:
        target_appt = execute_one("SELECT patient_id, doctor_id FROM appointment WHERE appointment_id = %s", (preselect_appointment_id,))
        if target_appt:
            preselect_patient_id = target_appt["patient_id"]
            preselect_doctor_id = target_appt["doctor_id"]

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_id = request.form.get("appointment_id")
        diagnosis = request.form.get("diagnosis", "").strip()
        prescription = request.form.get("prescription", "").strip() or None
        report = request.form.get("report", "").strip() or None
        record_date_raw = request.form.get("record_date", "").strip()

        if not patient_id or not doctor_id or not appointment_id or not diagnosis:
            flash("Patient, Doctor, Appointment, and Diagnosis fields are required.", "danger")
            return render_template(
                "medical_record_form.html",
                record=None,
                patients=patients,
                doctors=doctors,
                appointments=appointments,
                form_data=request.form
            ), 400

        record_date = parse_date(record_date_raw) or date.today()

        # Referential Validation: Check that the appointment belongs to the chosen patient and doctor
        appt_check = execute_one("""
            SELECT patient_id, doctor_id 
            FROM appointment 
            WHERE appointment_id = %s
        """, (appointment_id,))

        if not appt_check:
            flash("Selected appointment does not exist.", "danger")
            return render_template("medical_record_form.html", record=None, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 400

        if str(appt_check["patient_id"]) != str(patient_id):
            flash("Relational Error: The selected appointment does not belong to the selected patient.", "danger")
            return render_template("medical_record_form.html", record=None, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 400

        if str(appt_check["doctor_id"]) != str(doctor_id):
            flash("Relational Error: The selected appointment does not belong to the selected doctor.", "danger")
            return render_template("medical_record_form.html", record=None, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 400

        try:
            execute_write("""
                INSERT INTO medical_record (patient_id, doctor_id, appointment_id, diagnosis, prescription, report, record_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, doctor_id, appointment_id, diagnosis, prescription, report, record_date))
            flash("Medical record recorded successfully!", "success")
            return redirect(url_for("medical_records_list"))
        except Exception as e:
            flash(f"Error creating medical record: {e}", "danger")
            return render_template("medical_record_form.html", record=None, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 500

    return render_template(
        "medical_record_form.html",
        record=None,
        patients=patients,
        doctors=doctors,
        appointments=appointments,
        preselect_appointment_id=preselect_appointment_id,
        preselect_patient_id=preselect_patient_id,
        preselect_doctor_id=preselect_doctor_id
    )


@app.route("/medical-records/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def medical_record_edit(record_id):
    """Edit existing medical record."""
    record = execute_one("SELECT * FROM medical_record WHERE record_id = %s", (record_id,))
    if not record:
        flash("Record not found.", "warning")
        return redirect(url_for("medical_records_list"))

    patients = execute_query("SELECT patient_id, name FROM patient ORDER BY name ASC")
    doctors = execute_query("SELECT doctor_id, name, specialization FROM doctor ORDER BY name ASC")
    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.doctor_id,
            d.name AS doctor_name,
            a.appointment_date
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        INNER JOIN doctor d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """)

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_id = request.form.get("appointment_id")
        diagnosis = request.form.get("diagnosis", "").strip()
        prescription = request.form.get("prescription", "").strip() or None
        report = request.form.get("report", "").strip() or None
        record_date_raw = request.form.get("record_date", "").strip()

        if not patient_id or not doctor_id or not appointment_id or not diagnosis:
            flash("Patient, Doctor, Appointment, and Diagnosis fields are required.", "danger")
            return render_template("medical_record_form.html", record=record, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 400

        record_date = parse_date(record_date_raw) or record["record_date"]

        appt_check = execute_one("SELECT patient_id, doctor_id FROM appointment WHERE appointment_id = %s", (appointment_id,))
        if not appt_check or str(appt_check["patient_id"]) != str(patient_id) or str(appt_check["doctor_id"]) != str(doctor_id):
            flash("Relational Error: The selected appointment does not belong to the selected patient and doctor.", "danger")
            return render_template("medical_record_form.html", record=record, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 400

        try:
            execute_write("""
                UPDATE medical_record
                SET patient_id = %s, doctor_id = %s, appointment_id = %s, diagnosis = %s, prescription = %s, report = %s, record_date = %s
                WHERE record_id = %s
            """, (patient_id, doctor_id, appointment_id, diagnosis, prescription, report, record_date, record_id))
            flash("Medical record updated.", "success")
            return redirect(url_for("medical_record_detail", record_id=record_id))
        except Exception as e:
            flash(f"Error updating record: {e}", "danger")
            return render_template("medical_record_form.html", record=record, patients=patients, doctors=doctors, appointments=appointments, form_data=request.form), 500

    return render_template(
        "medical_record_form.html",
        record=record,
        patients=patients,
        doctors=doctors,
        appointments=appointments
    )


@app.route("/medical-records/<int:record_id>/delete", methods=["POST"])
@login_required
def medical_record_delete(record_id):
    """Delete a medical record safely."""
    record = execute_one("SELECT * FROM medical_record WHERE record_id = %s", (record_id,))
    if not record:
        flash("Record not found.", "warning")
        return redirect(url_for("medical_records_list"))

    try:
        execute_write("DELETE FROM medical_record WHERE record_id = %s", (record_id,))
        flash("Medical record deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting record: {e}", "danger")

    return redirect(url_for("medical_records_list"))


# ==========================================================================
# 6. BILLING & INVOICE MANAGEMENT MODULE (PROTECTED)
# ==========================================================================
@app.route("/billing")
@login_required
def billing_list():
    """
    Display billing records with revenue totals, patient searches,
    and payment status filtering.
    """
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    # Aggregate Revenue KPI metrics
    revenue_stats = execute_one("""
        SELECT 
            COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN amount ELSE 0 END), 0) AS paid_revenue,
            COALESCE(SUM(CASE WHEN payment_status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_revenue,
            COALESCE(SUM(CASE WHEN payment_status = 'Partially Paid' THEN amount ELSE 0 END), 0) AS partial_revenue,
            COUNT(*) AS total_bills
        FROM billing
    """)

    sql = """
        SELECT 
            b.bill_id,
            b.patient_id,
            p.name AS patient_name,
            b.appointment_id,
            a.appointment_date,
            d.name AS doctor_name,
            b.amount,
            b.payment_status,
            b.insurance_details,
            b.bill_date
        FROM billing b
        INNER JOIN patient p ON b.patient_id = p.patient_id
        INNER JOIN appointment a ON b.appointment_id = a.appointment_id
        LEFT JOIN doctor d ON a.doctor_id = d.doctor_id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND p.name LIKE %s"
        params.append(f"%{q}%")
    if status:
        sql += " AND b.payment_status = %s"
        params.append(status)

    sql += " ORDER BY b.bill_date DESC, b.bill_id DESC"
    bills = execute_query(sql, params)

    filters = {"q": q, "status": status}

    return render_template(
        "billing.html",
        bills=bills,
        revenue_stats=revenue_stats,
        filters=filters
    )


@app.route("/billing/<int:bill_id>")
@login_required
def billing_detail(bill_id):
    """View detailed printable hospital invoice."""
    bill = execute_one("""
        SELECT 
            b.*,
            p.name AS patient_name,
            p.phone AS patient_phone,
            p.address AS patient_address,
            a.appointment_date,
            d.name AS doctor_name,
            d.department
        FROM billing b
        INNER JOIN patient p ON b.patient_id = p.patient_id
        INNER JOIN appointment a ON b.appointment_id = a.appointment_id
        LEFT JOIN doctor d ON a.doctor_id = d.doctor_id
        WHERE b.bill_id = %s
    """, (bill_id,))

    if not bill:
        flash("Invoice not found.", "warning")
        return redirect(url_for("billing_list"))

    return render_template("billing_detail.html", bill=bill)


@app.route("/billing/add", methods=["GET", "POST"])
@login_required
def billing_add():
    """
    Generate a new bill.
    Validates that amount >= 0 and that appointment belongs to the chosen patient.
    """
    patients = execute_query("SELECT patient_id, name FROM patient ORDER BY name ASC")
    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.appointment_date
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """)

    preselect_appointment_id = request.args.get("appointment_id")
    preselect_patient_id = request.args.get("patient_id")

    if preselect_appointment_id and not preselect_patient_id:
        target_appt = execute_one("SELECT patient_id FROM appointment WHERE appointment_id = %s", (preselect_appointment_id,))
        if target_appt:
            preselect_patient_id = target_appt["patient_id"]

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        appointment_id = request.form.get("appointment_id")
        amount_raw = request.form.get("amount", "").strip()
        payment_status = request.form.get("payment_status", "Pending").strip()
        insurance_details = request.form.get("insurance_details", "").strip() or None
        bill_date_raw = request.form.get("bill_date", "").strip()

        if not patient_id or not appointment_id or not amount_raw:
            flash("Patient, Appointment, and Amount are required.", "danger")
            return render_template("billing_form.html", bill=None, patients=patients, appointments=appointments, form_data=request.form), 400

        amount = parse_decimal(amount_raw)
        if amount is None or amount < 0:
            flash("Validation Error: Bill amount must be a non-negative number.", "danger")
            return render_template("billing_form.html", bill=None, patients=patients, appointments=appointments, form_data=request.form), 400

        if payment_status not in ("Paid", "Pending", "Partially Paid"):
            flash("Invalid payment status.", "danger")
            return render_template("billing_form.html", bill=None, patients=patients, appointments=appointments, form_data=request.form), 400

        bill_date = parse_date(bill_date_raw) or date.today()

        # Validate that appointment belongs to the selected patient
        appt = execute_one("SELECT patient_id FROM appointment WHERE appointment_id = %s", (appointment_id,))
        if not appt or str(appt["patient_id"]) != str(patient_id):
            flash("Relational Integrity Error: The selected appointment does not belong to the selected patient.", "danger")
            return render_template("billing_form.html", bill=None, patients=patients, appointments=appointments, form_data=request.form), 400

        try:
            execute_write("""
                INSERT INTO billing (patient_id, appointment_id, amount, payment_status, insurance_details, bill_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (patient_id, appointment_id, amount, payment_status, insurance_details, bill_date))
            flash(f"Bill generated successfully for ₹{amount:,.2f}!", "success")
            return redirect(url_for("billing_list"))
        except Exception as e:
            flash(f"Error generating bill: {e}", "danger")
            return render_template("billing_form.html", bill=None, patients=patients, appointments=appointments, form_data=request.form), 500

    return render_template(
        "billing_form.html",
        bill=None,
        patients=patients,
        appointments=appointments,
        preselect_appointment_id=preselect_appointment_id,
        preselect_patient_id=preselect_patient_id
    )


@app.route("/billing/<int:bill_id>/edit", methods=["GET", "POST"])
@login_required
def billing_edit(bill_id):
    """Edit existing billing record."""
    bill = execute_one("SELECT * FROM billing WHERE bill_id = %s", (bill_id,))
    if not bill:
        flash("Bill not found.", "warning")
        return redirect(url_for("billing_list"))

    patients = execute_query("SELECT patient_id, name FROM patient ORDER BY name ASC")
    appointments = execute_query("""
        SELECT 
            a.appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.appointment_date
        FROM appointment a
        INNER JOIN patient p ON a.patient_id = p.patient_id
        ORDER BY a.appointment_date DESC, a.appointment_id DESC
    """)

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        appointment_id = request.form.get("appointment_id")
        amount_raw = request.form.get("amount", "").strip()
        payment_status = request.form.get("payment_status", "Pending").strip()
        insurance_details = request.form.get("insurance_details", "").strip() or None
        bill_date_raw = request.form.get("bill_date", "").strip()

        amount = parse_decimal(amount_raw)
        if amount is None or amount < 0:
            flash("Validation Error: Bill amount must be non-negative.", "danger")
            return render_template("billing_form.html", bill=bill, patients=patients, appointments=appointments, form_data=request.form), 400

        if payment_status not in ("Paid", "Pending", "Partially Paid"):
            flash("Invalid payment status.", "danger")
            return render_template("billing_form.html", bill=bill, patients=patients, appointments=appointments, form_data=request.form), 400

        bill_date = parse_date(bill_date_raw) or bill["bill_date"]

        appt = execute_one("SELECT patient_id FROM appointment WHERE appointment_id = %s", (appointment_id,))
        if not appt or str(appt["patient_id"]) != str(patient_id):
            flash("Relational Integrity Error: The selected appointment does not belong to the selected patient.", "danger")
            return render_template("billing_form.html", bill=bill, patients=patients, appointments=appointments, form_data=request.form), 400

        try:
            execute_write("""
                UPDATE billing
                SET patient_id = %s, appointment_id = %s, amount = %s, payment_status = %s, insurance_details = %s, bill_date = %s
                WHERE bill_id = %s
            """, (patient_id, appointment_id, amount, payment_status, insurance_details, bill_date, bill_id))
            flash(f"Invoice #{bill_id} updated.", "success")
            return redirect(url_for("billing_detail", bill_id=bill_id))
        except Exception as e:
            flash(f"Error updating bill: {e}", "danger")
            return render_template("billing_form.html", bill=bill, patients=patients, appointments=appointments, form_data=request.form), 500

    return render_template(
        "billing_form.html",
        bill=bill,
        patients=patients,
        appointments=appointments
    )


@app.route("/billing/<int:bill_id>/status", methods=["POST"])
@login_required
def billing_status_update(bill_id):
    """Quickly update payment status (e.g. mark as Paid)."""
    new_status = request.form.get("payment_status", "Paid").strip()
    if new_status not in ("Paid", "Pending", "Partially Paid"):
        flash("Invalid payment status.", "danger")
        return redirect(url_for("billing_list"))

    execute_write("UPDATE billing SET payment_status = %s WHERE bill_id = %s", (new_status, bill_id))
    flash(f"Invoice #{bill_id} status updated to {new_status}.", "success")
    return redirect(url_for("billing_list"))


@app.route("/billing/<int:bill_id>/delete", methods=["POST"])
@login_required
def billing_delete(bill_id):
    """Safely delete a bill."""
    bill = execute_one("SELECT * FROM billing WHERE bill_id = %s", (bill_id,))
    if not bill:
        flash("Bill not found.", "warning")
        return redirect(url_for("billing_list"))

    try:
        execute_write("DELETE FROM billing WHERE bill_id = %s", (bill_id,))
        flash(f"Invoice #{bill_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting bill: {e}", "danger")

    return redirect(url_for("billing_list"))


# ==========================================================================
# 7. ADMINISTRATOR USER MANAGEMENT
# ==========================================================================
@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """
    Administrative portal to inspect user accounts, manage roles,
    and maintain system access across Patient, Doctor, Staff, and Administrator roles.
    """
    users = execute_query("""
        SELECT user_id, name, email, phone, role, status, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    
    total_users = len(users)
    patient_count = sum(1 for u in users if u.get("role") == "Patient")
    doctor_count = sum(1 for u in users if u.get("role") == "Doctor")
    staff_count = sum(1 for u in users if u.get("role") == "Staff")
    admin_count = sum(1 for u in users if u.get("role") == "Administrator")
    
    return render_template(
        "admin_users.html",
        users=users,
        total_users=total_users,
        patient_count=patient_count,
        doctor_count=doctor_count,
        staff_count=staff_count,
        admin_count=admin_count,
        active_page="admin_users"
    )


@app.route("/admin/users/<int:user_id>/status", methods=["POST"])
@login_required
@admin_required
def admin_update_user_status(user_id):
    """Update user account status (Approved or Disabled)."""
    new_status = request.form.get("status", "").strip()
    if new_status not in ("Approved", "Disabled"):
        flash("Invalid status transition requested.", "danger")
        return redirect(url_for("admin_users"))

    target_user = execute_one("SELECT user_id, name, email, role, status FROM users WHERE user_id = %s", (user_id,))
    if not target_user:
        flash("User account not found.", "danger")
        return redirect(url_for("admin_users"))

    # Protection: Cannot modify status of own account
    if target_user["user_id"] == session.get("user_id"):
        flash("Safety restriction: You cannot modify the status of your own account.", "warning")
        return redirect(url_for("admin_users"))

    # Protection: If disabling an administrator, ensure at least one other active administrator exists
    if target_user["role"] == "Administrator" and new_status == "Disabled":
        admin_count = execute_one("""
            SELECT COUNT(*) AS total FROM users 
            WHERE role = 'Administrator' AND status = 'Approved' AND user_id != %s
        """, (user_id,))["total"]
        if admin_count < 1:
            flash("Safety restriction: Cannot deactivate the sole active Administrator account.", "danger")
            return redirect(url_for("admin_users"))

    execute_write("UPDATE users SET status = %s WHERE user_id = %s", (new_status, user_id))
    flash(f"Account for {target_user['name']} (<{target_user['email']}>) status updated to '{new_status}'.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def admin_update_user_role(user_id):
    """Assign or change user role among Patient, Doctor, Staff, and Administrator."""
    new_role = request.form.get("role", "").strip()
    if new_role not in ("Patient", "Doctor", "Staff", "Administrator"):
        flash("Invalid role requested.", "danger")
        return redirect(url_for("admin_users"))

    target_user = execute_one("SELECT user_id, name, email, role, status FROM users WHERE user_id = %s", (user_id,))
    if not target_user:
        flash("User account not found.", "danger")
        return redirect(url_for("admin_users"))

    # Protection: Cannot demote yourself if you are the last administrator
    if target_user["user_id"] == session.get("user_id") and new_role != "Administrator":
        admin_count = execute_one("""
            SELECT COUNT(*) AS total FROM users 
            WHERE role = 'Administrator' AND status = 'Approved' AND user_id != %s
        """, (user_id,))["total"]
        if admin_count < 1:
            flash("Safety restriction: Cannot remove administrative privileges from the sole Administrator.", "danger")
            return redirect(url_for("admin_users"))

    execute_write("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
    flash(f"Role for {target_user['name']} updated to '{new_role}'.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Safely remove a user account."""
    target_user = execute_one("SELECT user_id, name, email, role FROM users WHERE user_id = %s", (user_id,))
    if not target_user:
        flash("User account not found.", "danger")
        return redirect(url_for("admin_users"))

    if target_user["user_id"] == session.get("user_id"):
        flash("Safety restriction: You cannot delete your own account.", "warning")
        return redirect(url_for("admin_users"))

    if target_user["role"] == "Administrator":
        admin_count = execute_one("""
            SELECT COUNT(*) AS total FROM users 
            WHERE role = 'Administrator' AND user_id != %s
        """, (user_id,))["total"]
        if admin_count < 1:
            flash("Safety restriction: Cannot delete the sole Administrator account.", "danger")
            return redirect(url_for("admin_users"))

    execute_write("DELETE FROM users WHERE user_id = %s", (user_id,))
    flash(f"User account '{target_user['name']}' has been deleted.", "success")
    return redirect(url_for("admin_users"))


# ==========================================================================
# 8. SYSTEM HEALTH & API ENDPOINTS
# ==========================================================================
@app.route("/api/health")
def api_health():
    """Database connectivity and health check endpoint."""
    healthy, info = check_db_health()
    return jsonify({
        "status": "online" if healthy else "error",
        "database": info,
        "timestamp": datetime.now().isoformat()
    }), 200 if healthy else 500


if __name__ == "__main__":
    # College mini-project local server configuration
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    port = int(os.getenv("PORT", 5000))
    print(f"Starting CarePoint Hospital Management System on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=is_debug)
