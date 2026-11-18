"""
test_app.py - Automated Test Suite for CarePoint Hospital Management System
Tests authentication, route protection, landing page, login/logout workflows,
database connectivity, SQL joins, form validations, referential integrity safety,
and CRUD lifecycles.
"""

import sys
import os
import unittest
from datetime import date, timedelta
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database import get_db_connection, execute_one, execute_query, execute_write, init_users_table
from werkzeug.security import generate_password_hash


class CarePointHMSTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configure test client, initialize users table, and verify MySQL connectivity."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for programmatic POST testing
        cls.client = app.test_client()

        # Verify live database connection
        conn = get_db_connection()
        assert conn.is_connected(), "MySQL connection failed during test setup."
        conn.close()

        # Ensure users table exists and test admin account exists
        init_users_table()
        cls.admin_email = "admin@carepoint.health"
        cls.admin_password = "Admin@CarePoint2026"

        existing = execute_one("SELECT user_id FROM users WHERE email = %s", (cls.admin_email,))
        if not existing:
            execute_write("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, (
                "System Administrator",
                cls.admin_email,
                generate_password_hash(cls.admin_password),
                "Administrator"
            ))

    def setUp(self):
        """Ensure each test starts with a clean, isolated session."""
        with self.client.session_transaction() as sess:
            sess.clear()

    def login_admin(self):
        """Helper method to authenticate test client session as admin."""
        return self.client.post("/login", data={
            "email": self.admin_email,
            "password": self.admin_password
        }, follow_redirects=True)

    def test_01_db_connection_health(self):
        """Test database connection health endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("hospital_management", data["database"])

    def test_02_public_landing_page(self):
        """Test public landing page loads at '/' without authentication."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("Smarter Hospital Management, Better Patient Care.", html)
        self.assertIn("A centralized hospital management platform", html)
        self.assertIn("Get Started", html)
        self.assertIn("Explore Features", html)
        self.assertIn("Patient Management", html)
        self.assertIn("Doctor Management", html)
        self.assertIn("Appointment Scheduling", html)
        self.assertIn("Medical Records", html)
        self.assertIn("Billing Management", html)
        self.assertIn("CarePoint", html)

    def test_03_route_protection_unauthenticated_redirects(self):
        """Test that direct access to /dashboard and management modules is blocked without login."""
        protected_routes = [
            "/dashboard",
            "/patients",
            "/doctors",
            "/appointments",
            "/medical-records",
            "/billing"
        ]
        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route, follow_redirects=False)
                # Must be a 302 redirect to /login
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login", response.headers["Location"])

    def test_04_login_validation_invalid_credentials(self):
        """Test login fails with incorrect password or non-existent email."""
        # Incorrect password
        res1 = self.client.post("/login", data={
            "email": self.admin_email,
            "password": "WrongPassword!"
        })
        self.assertEqual(res1.status_code, 401)
        self.assertIn("Invalid email address or password", res1.get_data(as_text=True))

        # Unknown email
        res2 = self.client.post("/login", data={
            "email": "nonexistent@hospital.com",
            "password": "AnyPassword123"
        })
        self.assertEqual(res2.status_code, 401)
        self.assertIn("Invalid email address or password", res2.get_data(as_text=True))

        # Empty fields
        res3 = self.client.post("/login", data={"email": "", "password": ""})
        self.assertEqual(res3.status_code, 400)

    def test_05_login_success_and_open_redirect_protection(self):
        """Test successful login redirects to dashboard and blocks malicious external next URLs."""
        # Attempt open redirect attack: next=http://evil.com
        res = self.client.post("/login", data={
            "email": self.admin_email,
            "password": self.admin_password,
            "next": "http://evil.com"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        # Must be sanitized to local /dashboard
        self.assertEqual(res.headers["Location"], "/dashboard")

    def test_06_authenticated_dashboard_loads_real_data(self):
        """Test dashboard loads when authenticated, displaying real statistics and recent appointments."""
        self.login_admin()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("CarePoint", html)
        self.assertIn("Total Patients", html)
        self.assertIn("Active Doctors", html)
        self.assertIn("Recent Appointments", html)
        # Check that existing patients & doctors from MySQL appear
        self.assertIn("Aarav Sharma", html)
        self.assertIn("Dr. Amit Sharma", html)

    def test_07_logout_workflow(self):
        """Test logging out clears the session and redirects to public landing page."""
        self.login_admin()
        # Verify authenticated access
        res1 = self.client.get("/dashboard")
        self.assertEqual(res1.status_code, 200)

        # Log out - must redirect to landing page '/'
        res_logout = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        self.assertEqual(res_logout.headers["Location"], "/")

        # Attempt to access dashboard again - should be redirected to /login
        res2 = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(res2.status_code, 302)
        self.assertIn("/login", res2.headers["Location"])

    def test_08_patients_list_and_search_authenticated(self):
        """Test patients list page and search functionality under authentication."""
        self.login_admin()
        response = self.client.get("/patients")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Aarav Sharma", html)
        self.assertIn("Priya Verma", html)

        # Test search
        search_res = self.client.get("/patients?q=Aarav")
        self.assertEqual(search_res.status_code, 200)
        self.assertIn("Aarav Sharma", search_res.get_data(as_text=True))

    def test_09_patient_detail_relational_views(self):
        """Test viewing a patient detail displays their appointments, medical records, and bills."""
        self.login_admin()
        response = self.client.get("/patients/1")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Aarav Sharma", html)
        self.assertIn("Appointment History", html)
        self.assertIn("Clinical Medical Records", html)
        self.assertIn("Billing", html)

    def test_10_doctors_list_and_detail(self):
        """Test doctors directory and individual doctor profile."""
        self.login_admin()
        response = self.client.get("/doctors")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Dr. Amit Sharma", html)
        self.assertIn("Cardiology", html)

        doc_res = self.client.get("/doctors/1")
        self.assertEqual(doc_res.status_code, 200)
        doc_html = doc_res.get_data(as_text=True)
        self.assertIn("Dr. Amit Sharma", doc_html)
        self.assertIn("Cardiologist", doc_html)

    def test_11_appointments_list_and_filters(self):
        """Test appointments list, multi-criteria filtering, and detail view."""
        self.login_admin()
        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Appointments Directory", html)

        # Filter by status
        filt_res = self.client.get("/appointments?status=Scheduled")
        self.assertEqual(filt_res.status_code, 200)
        self.assertIn("Scheduled", filt_res.get_data(as_text=True))

        # Detail view
        detail_res = self.client.get("/appointments/1")
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn("Consultation Booking #1", detail_res.get_data(as_text=True))

    def test_12_medical_records_list_and_detail(self):
        """Test medical records directory and individual clinical record."""
        self.login_admin()
        response = self.client.get("/medical-records")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Clinical Records Directory", html)
        self.assertIn("Mild hypertension", html)

        # Detail view
        rec_res = self.client.get("/medical-records/1")
        self.assertEqual(rec_res.status_code, 200)
        rec_html = rec_res.get_data(as_text=True)
        self.assertIn("Clinical Diagnosis", rec_html)
        self.assertIn("Mild hypertension", rec_html)

    def test_13_billing_list_and_invoice_receipt(self):
        """Test billing ledger, revenue totals, and printable invoice receipt."""
        self.login_admin()
        response = self.client.get("/billing")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Invoices & Billing Ledger", html)
        self.assertIn("Total Paid Revenue", html)

        # Printable invoice
        inv_res = self.client.get("/billing/1")
        self.assertEqual(inv_res.status_code, 200)
        inv_html = inv_res.get_data(as_text=True)
        self.assertIn("OFFICIAL RECEIPT", inv_html)
        self.assertIn("CarePoint Hospital", inv_html)
        self.assertIn("1,500.00", inv_html)

    def test_14_form_validations_and_integrity_guards(self):
        """Test server-side rejection of invalid inputs and relational constraints."""
        self.login_admin()

        # 1. Empty patient name
        res_pat = self.client.post("/patients/add", data={"name": "", "gender": "Male"})
        self.assertEqual(res_pat.status_code, 400)
        self.assertIn("Patient full name is required", res_pat.get_data(as_text=True))

        # 2. Appointment in the past
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        res_apt = self.client.post("/appointments/add", data={
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_date": yesterday,
            "time_slot": "10:00 AM",
            "status": "Scheduled"
        })
        self.assertEqual(res_apt.status_code, 400)
        self.assertIn("Cannot schedule appointments in the past", res_apt.get_data(as_text=True))

        # 3. Negative billing amount
        res_bil = self.client.post("/billing/add", data={
            "patient_id": 1,
            "appointment_id": 1,
            "amount": "-500.00",
            "payment_status": "Pending"
        })
        self.assertEqual(res_bil.status_code, 400)
        self.assertIn("must be a non-negative number", res_bil.get_data(as_text=True))

        # 4. Medical record appointment patient mismatch
        res_med = self.client.post("/medical-records/add", data={
            "patient_id": 2,  # Mismatched!
            "doctor_id": 1,
            "appointment_id": 1,
            "diagnosis": "Test Diagnosis"
        })
        self.assertEqual(res_med.status_code, 400)
        self.assertIn("Relational Error", res_med.get_data(as_text=True))

    def test_15_referential_integrity_safe_deletion_blocking(self):
        """
        Verify that attempting to delete a patient who has dependent appointments,
        medical records, or bills is safely blocked to protect referential integrity.
        """
        self.login_admin()
        # Patient 1 has existing appointments, medical records, and bills
        response = self.client.post("/patients/1/delete", follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Referential Integrity Alert", html)
        self.assertIn("Cannot delete Patient", html)

        # Confirm patient 1 still exists in the database
        patient = execute_one("SELECT * FROM patient WHERE patient_id = 1")
        self.assertIsNotNone(patient)
        self.assertEqual(patient["name"], "Aarav Sharma")

    def test_16_safe_crud_lifecycle_temporary_record(self):
        """
        Test complete end-to-end CRUD on a standalone temporary patient.
        Ensures insert, read, update, and safe delete work properly without
        affecting any existing user data.
        """
        self.login_admin()
        temp_name = "Automated Test Patient"
        res_create = self.client.post("/patients/add", data={
            "name": temp_name,
            "gender": "Other",
            "dob": "1999-01-01",
            "phone": "9999900000",
            "address": "Temporary Test Suite Address"
        }, follow_redirects=True)
        self.assertEqual(res_create.status_code, 200)

        created_p = execute_one("SELECT * FROM patient WHERE name = %s", (temp_name,))
        self.assertIsNotNone(created_p)
        temp_id = created_p["patient_id"]

        try:
            res_edit = self.client.post(f"/patients/{temp_id}/edit", data={
                "name": "Updated Test Patient",
                "gender": "Other",
                "dob": "1999-01-01",
                "phone": "9999911111",
                "address": "Updated Address"
            }, follow_redirects=True)
            self.assertEqual(res_edit.status_code, 200)

            updated_p = execute_one("SELECT * FROM patient WHERE patient_id = %s", (temp_id,))
            self.assertEqual(updated_p["name"], "Updated Test Patient")
        finally:
            res_delete = self.client.post(f"/patients/{temp_id}/delete", follow_redirects=True)
            self.assertEqual(res_delete.status_code, 200)
            deleted_check = execute_one("SELECT * FROM patient WHERE patient_id = %s", (temp_id,))
            self.assertIsNone(deleted_check)

    def test_17_csrf_protection_enforcement(self):
        """Test that CSRF protection rejects requests without a valid token when enabled."""
        app.config["WTF_CSRF_ENABLED"] = True
        try:
            response = self.client.post("/login", data={"email": "attacker@evil.com", "password": "pass"})
            self.assertEqual(response.status_code, 400)
            self.assertIn("CSRF", response.get_data(as_text=True))
        finally:
            app.config["WTF_CSRF_ENABLED"] = False

    def test_18_404_handler(self):
        """Test 404 handler renders custom template for non-existent routes."""
        response = self.client.get("/non-existent-route-999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page Not Found", response.get_data(as_text=True))

    def test_19_signup_staff_immediate_approved(self):
        """Test public staff signup creates an account with status 'Approved' and enables immediate login."""
        test_email = "nurse.priya@carepoint.health"
        test_pass = "SecurePass2026!"
        test_phone = "9876543210"

        # Clean up in case record existed from prior test
        execute_write("DELETE FROM users WHERE email = %s", (test_email,))

        # Submit signup
        response = self.client.post("/signup", data={
            "name": "Nurse Priya Nair",
            "email": test_email,
            "phone": test_phone,
            "role": "Staff",
            "password": test_pass,
            "confirm_password": test_pass
        }, follow_redirects=False)

        # Must redirect to /login with flash
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("/login"))

        # Verify record in MySQL: immediately Approved without pending status
        user = execute_one("SELECT * FROM users WHERE email = %s", (test_email,))
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Nurse Priya Nair")
        self.assertEqual(user["role"], "Staff")
        self.assertEqual(user["phone"], test_phone)
        self.assertEqual(user["status"], "Approved")
        self.assertNotEqual(user["password_hash"], test_pass)
        self.assertTrue(user["password_hash"].startswith("scrypt:"))

    def test_20_immediate_login_without_admin_approval(self):
        """Test that a newly registered user logs in immediately without administrator approval."""
        test_email = "nurse.priya@carepoint.health"
        test_pass = "SecurePass2026!"

        login_res = self.client.post("/login", data={
            "email": test_email,
            "password": test_pass
        }, follow_redirects=True)

        self.assertEqual(login_res.status_code, 200)
        html = login_res.get_data(as_text=True)
        self.assertIn("Hospital Administration Dashboard", html)
        self.assertNotIn("pending administrator approval", html)

    def test_21_signup_patient_and_dashboard_redirect(self):
        """Test public patient registration and redirection to the dedicated Patient Portal."""
        pat_email = "patient.rahul@carepoint.health"
        pat_pass = "PatientPass2026!"
        pat_phone = "9812345678"

        execute_write("DELETE FROM users WHERE email = %s", (pat_email,))
        execute_write("DELETE FROM patient WHERE phone = %s", (pat_phone,))

        reg_res = self.client.post("/signup", data={
            "name": "Rahul Verma",
            "email": pat_email,
            "phone": pat_phone,
            "role": "Patient",
            "password": pat_pass,
            "confirm_password": pat_pass
        }, follow_redirects=False)

        self.assertEqual(reg_res.status_code, 302)

        # Verify automatic patient profile creation in patient table
        pat_record = execute_one("SELECT * FROM patient WHERE phone = %s", (pat_phone,))
        self.assertIsNotNone(pat_record)
        self.assertEqual(pat_record["name"], "Rahul Verma")

        # Log in as Patient
        login_res = self.client.post("/login", data={
            "email": pat_email,
            "password": pat_pass
        }, follow_redirects=True)

        self.assertEqual(login_res.status_code, 200)
        html = login_res.get_data(as_text=True)
        self.assertIn("Patient Portal", html)
        self.assertIn("Rahul Verma", html)

    def test_22_signup_doctor_and_dashboard_redirect(self):
        """Test public doctor registration and redirection to the Doctor Consultation Portal."""
        doc_email = "dr.ananya@carepoint.health"
        doc_pass = "DoctorPass2026!"
        doc_phone = "9823456789"

        execute_write("DELETE FROM users WHERE email = %s", (doc_email,))
        execute_write("DELETE FROM doctor WHERE email = %s", (doc_email,))

        reg_res = self.client.post("/signup", data={
            "name": "Dr. Ananya Roy",
            "email": doc_email,
            "phone": doc_phone,
            "role": "Doctor",
            "password": doc_pass,
            "confirm_password": doc_pass
        }, follow_redirects=False)

        self.assertEqual(reg_res.status_code, 302)

        # Verify automatic doctor profile creation in doctor table
        doc_record = execute_one("SELECT * FROM doctor WHERE email = %s", (doc_email,))
        self.assertIsNotNone(doc_record)
        self.assertEqual(doc_record["name"], "Dr. Ananya Roy")

        # Log in as Doctor
        login_res = self.client.post("/login", data={
            "email": doc_email,
            "password": doc_pass
        }, follow_redirects=True)

        self.assertEqual(login_res.status_code, 200)
        html = login_res.get_data(as_text=True)
        self.assertIn("Doctor Consultation Portal", html)
        self.assertIn("Dr. Ananya Roy", html)

    def test_23_signup_validations_and_duplicate_rejection(self):
        """Test validation rules on signup (duplicate email, mismatch, length, role security)."""
        # 1. Duplicate email (admin already exists) -> 409 Conflict
        res_dup = self.client.post("/signup", data={
            "name": "Duplicate Tester",
            "email": self.admin_email,
            "phone": "9998887776",
            "role": "Staff",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res_dup.status_code, 409)
        self.assertIn("already exists", res_dup.get_data(as_text=True))

        # 2. Password mismatch -> 400 Bad Request
        res_mis = self.client.post("/signup", data={
            "name": "Mismatch Tester",
            "email": "mismatch@carepoint.health",
            "phone": "9998887775",
            "role": "Staff",
            "password": "Password123!",
            "confirm_password": "DifferentPassword!"
        })
        self.assertEqual(res_mis.status_code, 400)
        self.assertIn("do not match", res_mis.get_data(as_text=True))

        # 3. Short password (< 8 chars) -> 400 Bad Request
        res_short = self.client.post("/signup", data={
            "name": "Short Pass Tester",
            "email": "short@carepoint.health",
            "phone": "9998887774",
            "role": "Staff",
            "password": "short",
            "confirm_password": "short"
        })
        self.assertEqual(res_short.status_code, 400)
        self.assertIn("at least 8 characters", res_short.get_data(as_text=True))

        # 4. Attempting to select Administrator in public signup -> 400 Bad Request
        res_admin = self.client.post("/signup", data={
            "name": "Fake Admin",
            "email": "fakeadmin@carepoint.health",
            "phone": "9998887773",
            "role": "Administrator",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res_admin.status_code, 400)
        self.assertIn("Invalid role selected", res_admin.get_data(as_text=True))

    def test_24_forgot_and_reset_password_flow(self):
        """Test full password reset workflow: request link, token validation, password update."""
        target_email = "nurse.priya@carepoint.health"
        new_password = "NewPriyaPass2026!"

        # 1. Request password reset
        req_res = self.client.post("/forgot-password", data={"email": target_email})
        self.assertEqual(req_res.status_code, 200)

        # Retrieve token from password_resets table
        reset_entry = execute_one("""
            SELECT r.* FROM password_resets r
            JOIN users u ON r.user_id = u.user_id
            WHERE u.email = %s AND r.used = 0
            ORDER BY r.created_at DESC LIMIT 1
        """, (target_email,))
        self.assertIsNotNone(reset_entry)
        token = reset_entry["token"]

        # 2. View reset password page
        view_res = self.client.get(f"/reset-password?token={token}")
        self.assertEqual(view_res.status_code, 200)
        self.assertIn("Reset Password", view_res.get_data(as_text=True))

        # 3. Submit new password
        post_res = self.client.post("/reset-password", data={
            "token": token,
            "password": new_password,
            "confirm_password": new_password
        }, follow_redirects=False)
        self.assertEqual(post_res.status_code, 302)

        # 4. Verify token is now marked used
        updated_token = execute_one("SELECT used FROM password_resets WHERE token = %s", (token,))
        self.assertEqual(updated_token["used"], 1)

        # 5. Verify old password fails
        old_login = self.client.post("/login", data={
            "email": target_email,
            "password": "SecurePass2026!"
        })
        self.assertEqual(old_login.status_code, 401)

        # 6. Verify new password succeeds
        new_login = self.client.post("/login", data={
            "email": target_email,
            "password": new_password
        }, follow_redirects=True)
        self.assertEqual(new_login.status_code, 200)
        self.assertIn("Hospital Administration Dashboard", new_login.get_data(as_text=True))

    def test_25_staff_forbidden_from_admin_pages(self):
        """Test non-admin users cannot access /admin/users."""
        target_email = "nurse.priya@carepoint.health"
        target_pass = "NewPriyaPass2026!"

        # Authenticate as staff
        self.client.post("/login", data={
            "email": target_email,
            "password": target_pass
        }, follow_redirects=True)

        # Attempt to access admin page
        admin_res = self.client.get("/admin/users", follow_redirects=True)
        self.assertEqual(admin_res.status_code, 200)
        self.assertIn("Administrator privileges are required", admin_res.get_data(as_text=True))

    def test_26_disabled_account_cannot_login(self):
        """Test that disabled accounts are blocked with 403 Forbidden."""
        dis_email = "disabled.user@carepoint.health"
        dis_pass = "DisabledPass2026!"

        execute_write("DELETE FROM users WHERE email = %s", (dis_email,))
        execute_write("""
            INSERT INTO users (name, email, password_hash, role, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ("Disabled Account", dis_email, generate_password_hash(dis_pass), "Staff", "Disabled"))

        res = self.client.post("/login", data={
            "email": dis_email,
            "password": dis_pass
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("deactivated", res.get_data(as_text=True))

    def test_27_admin_safety_protections(self):
        """Test safety guards prevent self-deletion and deactivating sole administrator."""
        self.login_admin()
        admin_user = execute_one("SELECT user_id FROM users WHERE email = %s", (self.admin_email,))

        # 1. Attempt self-status change
        res_stat = self.client.post(f"/admin/users/{admin_user['user_id']}/status", data={
            "status": "Disabled"
        }, follow_redirects=True)
        self.assertIn("cannot modify the status of your own account", res_stat.get_data(as_text=True))

        # 2. Attempt self-deletion
        res_del = self.client.post(f"/admin/users/{admin_user['user_id']}/delete", follow_redirects=True)
        self.assertIn("cannot delete your own account", res_del.get_data(as_text=True))

    def test_28_analytics_api_route_protection(self):
        """Test unauthenticated requests to /api/dashboard/analytics are rejected with redirect to login."""
        response = self.client.get("/api/dashboard/analytics", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_29_analytics_api_authenticated_data_and_schema(self):
        """Test authenticated staff/admin can fetch complete visual analytics metrics and charts."""
        self.login_admin()
        response = self.client.get("/api/dashboard/analytics?range=this_month")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("range", data)
        self.assertIn("stats", data)

        # 4 KPI summary cards
        stats = data["stats"]
        self.assertIn("total_patients", stats)
        self.assertIn("total_doctors", stats)
        self.assertIn("total_appointments", stats)
        self.assertIn("total_revenue", stats)
        self.assertGreater(stats["total_patients"], 0)
        self.assertGreater(stats["total_doctors"], 0)

        # 6 Charts verification
        self.assertIn("appointment_trends", data)
        self.assertIn("labels", data["appointment_trends"])
        self.assertIn("total", data["appointment_trends"])

        self.assertIn("appointment_status", data)
        self.assertIn("labels", data["appointment_status"])
        self.assertIn("percentages", data["appointment_status"])

        self.assertIn("patient_registrations", data)
        self.assertIn("labels", data["patient_registrations"])
        self.assertIn("counts", data["patient_registrations"])

        self.assertIn("revenue_trends", data)
        self.assertIn("labels", data["revenue_trends"])
        self.assertIn("collected", data["revenue_trends"])

        self.assertIn("doctor_appointments", data)
        self.assertIn("labels", data["doctor_appointments"])

        self.assertIn("department_appointments", data)
        self.assertIn("labels", data["department_appointments"])

        # Recent activities
        self.assertIn("recent_appointments", data)
        self.assertIn("recent_patients", data)
        self.assertGreater(len(data["recent_appointments"]), 0)
        self.assertGreater(len(data["recent_patients"]), 0)

    def test_30_analytics_api_date_range_filters(self):
        """Test analytics API responds correctly to all 5 required date-range filters."""
        self.login_admin()
        filter_options = ["today", "last_7_days", "last_30_days", "this_month"]
        for opt in filter_options:
            with self.subTest(range_opt=opt):
                res = self.client.get(f"/api/dashboard/analytics?range={opt}")
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data["success"])
                self.assertEqual(data["range"]["type"], opt)

        # Custom date range
        res_custom = self.client.get("/api/dashboard/analytics?range=custom&start_date=2026-10-01&end_date=2026-10-31")
        self.assertEqual(res_custom.status_code, 200)
        custom_data = res_custom.get_json()
        self.assertTrue(custom_data["success"])
        self.assertEqual(custom_data["range"]["type"], "custom")
        self.assertEqual(custom_data["range"]["start_date"], "2026-10-01")
        self.assertEqual(custom_data["range"]["end_date"], "2026-10-31")

    def test_31_analytics_patient_role_forbidden(self):
        """Test patients cannot access the administrative visual analytics API."""
        pat_email = "patient.rahul@carepoint.health"
        pat_pass = "PatientPass2026!"

        # Authenticate as patient
        self.client.post("/login", data={"email": pat_email, "password": pat_pass}, follow_redirects=True)

        # Attempt to access administrative analytics API
        res = self.client.get("/api/dashboard/analytics", follow_redirects=False)
        # Should be redirected to patient dashboard (302)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/dashboard/patient", res.headers["Location"])


if __name__ == "__main__":
    unittest.main()

