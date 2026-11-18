# Testing Documentation & Quality Assurance Report

## CarePoint Hospital Management System

---

## 1. Testing Strategy & Methodology

The testing phase for the CarePoint Hospital Management System incorporates a multi-tier verification methodology:
1. **Unit Testing**: Validating isolated logic components (password hashing, CSRF token generation, parameter parsing, query formatting).
2. **Integration Testing**: Verifying database interactions, transactional consistency, session creation, and cross-table foreign key constraints against a live MySQL test instance.
3. **Security Testing**: Evaluating authentication protection, password hashing hardness (`scrypt`), unauthenticated route interception, CSRF validation, open redirect prevention, and SQL injection resilience.
4. **End-to-End Functional Testing**: Validating user workflows from public landing page through login, dashboard exploration, and clinical management modules.

---

## 2. Test Environment Configuration

- **Testing Framework**: `pytest` / Python standard `unittest`
- **Application Runner**: Flask Test Client (`app.test_client()`)
- **Database Backend**: MySQL 8.0 running on `localhost:3306`
- **Python Version**: 3.14.6 (Windows 11)
- **Test Suite Location**: `D:\HMS\tests\test_app.py`
- **Execution Command**:
  ```bash
  python -m pytest -v tests/test_app.py
  ```

---

## 3. Comprehensive Test Case Matrix

| Test ID | Test Category | Module / Target | Test Description & Inputs | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Functional | Public Landing | `GET /` without active session | Returns HTTP 200; displays hero title, service feature cards, CarePoint branding; no patient data exposed. | HTTP 200; rendered `landing.html`; no private data. | **PASS** |
| **TC-02** | Functional | Authentication | `GET /login` | Returns HTTP 200; displays email/password fields, show/hide password toggle, CSRF hidden input. | HTTP 200; form rendered with valid CSRF token. | **PASS** |
| **TC-03** | Security | Authorization | `GET /dashboard` without login | Returns HTTP 302 redirect to `/login?next=%2Fdashboard`. | Redirected to `/login?next=%2Fdashboard`. | **PASS** |
| **TC-04** | Security | Route Protection | `GET /patients`, `/doctors`, `/appointments`, `/medical-records`, `/billing` (Unauthenticated) | Every protected endpoint responds with HTTP 302 redirect to `/login`. | All 5 module routes intercepted and redirected to `/login`. | **PASS** |
| **TC-05** | Security | Authentication | `POST /login` with registered email and incorrect password | Returns HTTP 200/302; flashes generic warning *"Invalid email or password."*; no session created. | Generic flash displayed; session remains unauthenticated. | **PASS** |
| **TC-06** | Security | Authentication | `POST /login` with non-existent email | Returns generic error without disclosing whether the email exists in the system. | Identical generic flash displayed (no user enumeration). | **PASS** |
| **TC-07** | Security | Authentication | `POST /login` with valid email (`admin@carepoint.health`) and valid password | Hash verification succeeds; session initialized with `user_id`, `user_name`, `user_role`; redirects to `/dashboard`. | Session populated; redirected to `/dashboard`; HTTP 302. | **PASS** |
| **TC-08** | Security | Session Mgmt | `GET /logout` with active session | Session cleared; session cookie invalidated; flashes logout message; redirects to `/login`. | Session purged; redirected to `/login`. | **PASS** |
| **TC-09** | Functional | Dashboard | `GET /dashboard` with active session | Returns HTTP 200; executes live aggregate queries; displays KPI metrics (Patients, Doctors, Appointments, Revenue). | HTTP 200; rendered dashboard with live MySQL metrics. | **PASS** |
| **TC-10** | Database | Patient Module | Register patient via `POST /patients/add` with demographic fields | Executes parameterized `INSERT INTO patient`; record persists in MySQL; patient count increments. | Record successfully created in MySQL table. | **PASS** |
| **TC-11** | Database | Doctor Module | `GET /doctors` with department filter | Executes `SELECT * FROM doctor WHERE department = %s`; returns filtered doctor listing. | Correct doctors displayed for selected department. | **PASS** |
| **TC-12** | Database | Appointments | `POST /appointments/add` with valid `patient_id` and `doctor_id` | Foreign keys validated; appointment inserted with status `Scheduled`. | Row created; visible in appointment calendar view. | **PASS** |
| **TC-13** | Database | Medical Records | `POST /medical-records/add` with diagnosis and prescription | Record inserted linking patient, doctor, and appointment; persists timestamp. | Record saved and displayed in patient clinical history. | **PASS** |
| **TC-14** | Database | Billing Module | `POST /billing/add` and toggle payment status to `Paid` | Invoice created with `amount`; status update reflected in gross revenue calculation. | Bill persisted; dashboard revenue KPI reflects updated sum. | **PASS** |
| **TC-15** | Security | CSRF Defense | `POST /login` without CSRF token (when CSRF enforcement is enabled) | Request rejected with HTTP 400 Bad Request; form tampering prevented. | HTTP 400 Bad Request returned; state change blocked. | **PASS** |
| **TC-16** | Security | Password Storage | Inspect `users` table after creating user via `create_admin.py` | Password field contains salted cryptographic hash (starts with `scrypt:`); plaintext password is never stored. | Cryptographic hash confirmed in MySQL; plaintext absent. | **PASS** |
| **TC-17** | Security | Injection Defense | Submit SQL injection payloads in search/inputs (e.g. `' OR 1=1 --`) | Parameterized queries prevent payload evaluation; treated as literal string literals. | Query executed safely with zero syntax distortion. | **PASS** |
| **TC-18** | Integrity | Foreign Key Safety | Delete patient who has active appointments or bills | Application checks child tables; intercepts deletion; shows friendly warning without MySQL Error 1451 crash. | Deletion blocked gracefully; warning presented to user. | **PASS** |
| **TC-19** | Auth/Signup | Self-Registration | Public submission to `POST /signup` with valid staff credentials | Inserts record into `users` with `role='Staff'` and `status='Pending'`; hashes password via `scrypt`; redirects to `/login`. | User created with status Pending; redirected to `/login`. | **PASS** |
| **TC-20** | Auth/Signup | Form Validations | Attempt signup with duplicate email, mismatched passwords, or short password (<8 chars) | Server rejects invalid submissions with HTTP 400/409 and descriptive flash messages. | Input validation enforced; duplicate email rejected (409). | **PASS** |
| **TC-21** | Auth/Login | Pending Protection | User with `status='Pending'` attempts to log in at `/login` | Access rejected with HTTP 403; flashes notice that administrator approval is required; no session created. | Pending account rejected with 403; protected modules blocked. | **PASS** |
| **TC-22** | Admin/Users | Approval Flow | Administrator reviews pending users and submits approval status update | Updates `users.status` to `'Approved'`; transaction committed in MySQL. | Status updated to `'Approved'` in database. | **PASS** |
| **TC-23** | Auth/Login | Approved Staff Access | Newly approved staff logs in with valid credentials | Session established; redirected to `/dashboard`; allowed access to `/patients`, `/appointments`, etc. | Approved staff logs in successfully; management modules load (200). | **PASS** |
| **TC-24** | Auth/RBAC | Role Isolation | Staff account attempts to navigate to `/admin/users` | Intercepted by `@admin_required`; redirected to `/dashboard` with warning flash. | Staff blocked from administrative user portal. | **PASS** |
| **TC-25** | Admin/Safety | Safety Invariants | Administrator attempts to delete own account or demote sole active administrator | Application blocks self-deletion and sole admin deactivation. | Safety invariants enforced; destructive action blocked. | **PASS** |

---

## 4. Test Execution Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-8.4.1, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: D:\HMS
plugins: anyio-4.14.0, platformdirs-4.12.1
collected 25 items

tests/test_app.py::CarePointHMSTestCase::test_01_db_connection_health PASSED [  4%]
tests/test_app.py::CarePointHMSTestCase::test_02_public_landing_page PASSED [  8%]
tests/test_app.py::CarePointHMSTestCase::test_03_route_protection_unauthenticated_redirects PASSED [ 12%]
tests/test_app.py::CarePointHMSTestCase::test_04_login_validation_invalid_credentials PASSED [ 16%]
tests/test_app.py::CarePointHMSTestCase::test_05_login_success_and_open_redirect_protection PASSED [ 20%]
tests/test_app.py::CarePointHMSTestCase::test_06_authenticated_dashboard_loads_real_data PASSED [ 24%]
tests/test_app.py::CarePointHMSTestCase::test_07_logout_workflow PASSED  [ 28%]
tests/test_app.py::CarePointHMSTestCase::test_08_patients_list_and_search_authenticated PASSED [ 32%]
tests/test_app.py::CarePointHMSTestCase::test_09_patient_detail_relational_views PASSED [ 36%]
tests/test_app.py::CarePointHMSTestCase::test_10_doctors_list_and_detail PASSED [ 40%]
tests/test_app.py::CarePointHMSTestCase::test_11_appointments_list_and_filters PASSED [ 44%]
tests/test_app.py::CarePointHMSTestCase::test_12_medical_records_list_and_detail PASSED [ 48%]
tests/test_app.py::CarePointHMSTestCase::test_13_billing_list_and_invoice_receipt PASSED [ 52%]
tests/test_app.py::CarePointHMSTestCase::test_14_form_validations_and_integrity_guards PASSED [ 56%]
tests/test_app.py::CarePointHMSTestCase::test_15_referential_integrity_safe_deletion_blocking PASSED [ 60%]
tests/test_app.py::CarePointHMSTestCase::test_16_safe_crud_lifecycle_temporary_record PASSED [ 64%]
tests/test_app.py::CarePointHMSTestCase::test_17_csrf_protection_enforcement PASSED [ 68%]
tests/test_app.py::CarePointHMSTestCase::test_18_404_handler PASSED      [ 72%]
tests/test_app.py::CarePointHMSTestCase::test_19_signup_validation_and_creation PASSED [ 76%]
tests/test_app.py::CarePointHMSTestCase::test_20_signup_validations_and_duplicate_rejection PASSED [ 80%]
tests/test_app.py::CarePointHMSTestCase::test_21_pending_account_cannot_login PASSED [ 84%]
tests/test_app.py::CarePointHMSTestCase::test_22_admin_user_management_and_approval PASSED [ 88%]
tests/test_app.py::CarePointHMSTestCase::test_23_approved_staff_can_login_and_access_modules PASSED [ 92%]
tests/test_app.py::CarePointHMSTestCase::test_24_staff_forbidden_from_admin_pages PASSED [ 96%]
tests/test_app.py::CarePointHMSTestCase::test_25_admin_safety_protections PASSED [100%]

============================= 25 passed in 21.25s =============================
```

- **Total Test Cases**: 25
- **Passed**: 25 (100%)
- **Failed**: 0 (0%)
- **Skipped**: 0 (0%)
- **Test Execution Time**: 21.25 seconds
- **Database State**: Zero data corruption; test records cleanly removed post-execution.

---

## 5. Security & Verification Summary

1. **Authentication Rigor**: Plaintext credentials are rejected by design. The system mandates `scrypt` hashing with secure salting via `werkzeug.security`.
2. **Access Control**: Every operational route (`/dashboard`, `/patients`, `/doctors`, `/appointments`, `/medical-records`, `/billing`) is guarded by the `@login_required` decorator.
3. **Session Invalidation**: Calling `/logout` strips session keys server-side and instructs the browser to drop the session cookie.
4. **Relational Resilience**: Foreign key constraints in MySQL are respected; cascading failures are avoided via explicit child-table existence pre-checks.

