# CarePoint - Hospital Management System (HMS)

> A modern, full-stack, college-level DBMS mini-project built with **Python Flask**, **MySQL**, and **Vanilla HTML5/CSS3/JavaScript**.

---

## 1. Project Overview

**CarePoint** is an enterprise-grade Hospital Management System designed for hospital administration personnel to manage patients, medical doctors, appointments, clinical records, and billing through a unified web portal.

The application features:
- **Public Landing Page** (`/`): Introduces hospital services, key features, and platform mission.
- **Staff Registration** (`/signup`): Secure self-registration with strong password enforcement, defaulting to `Staff` role and `Pending` status.
- **Secure Authentication** (`/login`): Salted `scrypt` password hashing, CSRF protection, status validation, and session guards.
- **Protected Administrative Dashboard** (`/dashboard`): Real-time SQL aggregate KPIs and recent appointments feed.
- **User Governance Portal** (`/admin/users`): Administrator portal to review pending staff, approve/reject registrations, toggle roles, and manage active status.
- **Protected Management Modules**:
  - Patient Directory & History (`/patients`)
  - Doctor Directory & Department Filters (`/doctors`)
  - Appointment Scheduling & Status Tracking (`/appointments`)
  - Electronic Medical Records (`/medical-records`)
  - Invoices & Revenue Ledger (`/billing`)
- **Safe Administrative CLI** (`create_admin.py`): Command-line utility to provision administrator credentials securely without plaintext password storage.

---

## 2. Key Modules & DBMS Concepts

| Module | Route | Access | DBMS Concepts & Features |
|---|---|---|---|
| **Landing Page** | `/` | Public | Modern presentation of hospital capabilities; links to login and signup; zero private data exposure. |
| **Staff Registration** | `/signup` | Public | Validates input format, checks email uniqueness in MySQL (HTTP 409 rejection on duplicate), hashes password via `scrypt`, stores as `Pending`. |
| **Authentication** | `/login`, `/logout` | Public / Auth | Cryptographic password hashing (`scrypt`), CSRF tokens, session state management, account status enforcement (`Pending`, `Approved`, `Rejected`, `Disabled`). |
| **User Administration** | `/admin/users` | Admin Only | Review pending staff applications, approve/reject registrations, promote/demote roles, with guards preventing self-deletion or demoting sole administrator. |
| **Dashboard** | `/dashboard` | Protected | Dynamic real-time metrics (`COUNT`, `SUM`), recent appointments feed (`INNER JOIN` across 3 tables), departmental activity distribution (`GROUP BY`), and billing status breakdown. |
| **Patient Management** | `/patients` | Protected | Complete CRUD operations, demographic data tracking, fast search by name or telephone number, detailed patient history view, and safe deletion with referential integrity guardrails. |
| **Doctor Management** | `/doctors` | Protected | Physician directory, specialty and department tracking, search by specialization/department, workload metrics (appointments per doctor using `LEFT JOIN`), and safe deletion protection. |
| **Appointment Scheduling** | `/appointments` | Protected | Interactive scheduling with patient and doctor dropdowns populated from MySQL, automated prevention of past appointments, and prevention of doctor time-slot double-booking. |
| **Medical Records** | `/medical-records` | Protected | Clinical charts with diagnosis, prescriptions, and lab examination reports. Relational validation guarantees an appointment belongs strictly to the selected patient and doctor. |
| **Billing & Invoices** | `/billing` | Protected | Comprehensive revenue ledger, tracking of Paid, Pending, and Partially Paid invoices, printable hospital receipts with print stylesheets, and non-negative amount validation. |

---

## 3. Technology Stack

- **Backend**: Python 3.14 (Flask Framework)
- **Database**: MySQL 8.0 (`hospital_management` schema)
- **Database Driver**: `mysql-connector-python`
- **Security**: Werkzeug (`generate_password_hash`, `check_password_hash` using `scrypt`), session cookies, CSRF protection
- **Frontend**: HTML5, CSS3 (Modern custom responsive dashboard styling), JavaScript (ES6)
- **Templating**: Jinja2 (Server-side rendering with custom context processors & filters)
- **Configuration**: `python-dotenv` for environment isolation

---

## 4. Database Architecture & Relationships

CarePoint operates on **six relational entities**: five operational entities plus a dedicated authentication entity:

```
+---------------+           +---------------+
|    patient    |           |    doctor     |
+---------------+           +---------------+
| * patient_id  |           | * doctor_id   |
|   name        |           |   name        |
|   gender      |           |   specialization
|   dob         |           |   phone       |
|   phone       |           |   email       |
|   address     |           |   department  |
+-------+-------+           +-------+-------+
        |                           |
        | 1                         | 1
        |                           |
        | N                         | N
+-------v---------------------------v-------+
|                appointment                |
+-------------------------------------------+
| * appointment_id                          |
| # patient_id (FK -> patient.patient_id)   |
| # doctor_id  (FK -> doctor.doctor_id)     |
|   appointment_date                        |
|   time_slot                               |
|   status (Scheduled, Completed, Cancelled)|
+-------+---------------------------+-------+
        |                           |
        | 1                         | 1
        |                           |
        | N                         | N
+-------v-----------------+ +-------v---------------------+
|     medical_record      | |           billing           |
+-------------------------+ +-----------------------------+
| * record_id             | | * bill_id                   |
| # patient_id    (FK)    | | # patient_id     (FK)       |
| # doctor_id     (FK)    | | # appointment_id (FK)       |
| # appointment_id(FK)    | |   amount                    |
|   diagnosis             | |   payment_status            |
|   prescription          | |   insurance_details         |
|   report                | |   bill_date                 |
|   record_date           | +-----------------------------+
+-------------------------+

+-------------------------------------------+
|                   users                   |
+-------------------------------------------+
| * user_id (PK, AUTO_INCREMENT)            |
|   name                                    |
|   email (UNIQUE)                          |
|   password_hash (scrypt salted hash)      |
|   role (Administrator, Staff)             |
|   status (Pending, Approved, etc.)        |
|   created_at (TIMESTAMP)                  |
+-------------------------------------------+
```

### Relational Constraints
- **One Patient to Many Appointments**: A patient can book multiple appointments over time.
- **One Doctor to Many Appointments**: A doctor can consult multiple patients across distinct time slots.
- **Clinical Records (1:N)**: Medical records strictly tie a patient, their attending physician, and the specific appointment session together.
- **Invoices (1:N)**: A billing record references both the patient and the completed appointment session.
- **Referential Integrity**: Child foreign keys utilize `NO ACTION` / `RESTRICT`. Deleting a patient or doctor with active dependent records is rejected with an explanation.

---

## 5. Project Directory Structure

```
D:\HMS\
│
├── app.py                     # Flask application entry point and route controllers
├── database.py                # Database connection utilities & query helpers
├── create_admin.py            # CLI script to provision administrator accounts safely
├── test_db.py                 # Quick database connectivity verification script
├── database_queries.sql       # Academic SQL demonstration script for reports & viva
├── requirements.txt           # Python dependencies
├── .env                       # Local environment variables (excluded from git)
├── .env.example               # Template environment configuration file
├── .gitignore                 # Git ignore rules for virtualenvs and secrets
├── README.md                  # Comprehensive project documentation
│
├── documentation/             # Complete Academic DBMS Documentation Suite
│   ├── README.md              # Documentation index and navigation map
│   ├── PROJECT_OVERVIEW.md    # Requirements, Scope, FRs & NFRs
│   ├── ER_DIAGRAM.md          # ER modeling with cardinalities and constraints
│   ├── DATA_FLOW_DIAGRAMS.md  # DFD Level-0 (Context) and Level-1 (Decomposed)
│   ├── SYSTEM_FLOWCHART.md    # End-to-end logical system flowchart
│   ├── USE_CASE_DIAGRAM.md    # UML Use Case specs & Actor traceability matrix
│   ├── DATABASE_DOCUMENTATION.md # Full Data Dictionary, Normalization (1NF-BCNF), Queries
│   ├── TESTING_DOCUMENTATION.md  # 18 Test Cases with execution log & pass verification
│   ├── PROJECT_REPORT.md      # Full 8-Chapter Academic Mini-Project Report
│   └── diagrams/              # Vector SVG & source diagram files
│       ├── er_diagram.svg     # Complete ER Diagram (6 tables, PKs, FKs, cardinalities)
│       ├── er_diagram.mmd     # Mermaid source for ER Diagram
│       ├── dfd_level0.svg     # Context Level-0 Data Flow Diagram
│       ├── dfd_level1.svg     # Decomposed Level-1 Data Flow Diagram
│       ├── system_flowchart.svg# System Flowchart with decision diamonds & loops
│       └── use_case_diagram.svg# UML Use Case Diagram with actors & relationships
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern dashboard & landing stylesheet
│   └── js/
│       └── main.js            # Client-side validation, password toggle, modals
│
├── templates/
│   ├── base.html              # Base layout with persistent sidebar and user badge
│   ├── landing.html           # Public landing page with hero, features & about
│   ├── signup.html            # Public staff registration portal with validation
│   ├── login.html             # Staff portal login form with CSRF and toggle
│   ├── dashboard.html         # Main overview with real-time SQL aggregate statistics
│   ├── admin_users.html       # Administrator user account management & approval portal
│   ├── patients.html          # Patient table with search and delete triggers
│   ├── patient_form.html      # Add / Edit patient demographic form
│   ├── patient_detail.html    # Patient profile with relational appointment & billing history
│   ├── doctors.html           # Doctor directory with department filters and metrics
│   ├── doctor_form.html       # Doctor onboarding form
│   ├── doctor_detail.html     # Doctor profile with assigned schedule
│   ├── appointments.html      # Appointment calendar directory with status filters
│   ├── appointment_form.html  # Appointment booking form with conflict validation
│   ├── appointment_detail.html# Consultation session view with clinical & billing shortcuts
│   ├── medical_records.html   # Clinical charts list with multi-table JOINs
│   ├── medical_record_form.html# Diagnosis, prescription, and examination report entry
│   ├── medical_record_detail.html# Full medical chart display
│   ├── billing.html           # Invoices ledger with revenue aggregate cards
│   ├── billing_form.html      # Hospital billing entry form
│   ├── billing_detail.html    # Printable receipt and formal invoice view
│   ├── 400.html               # Bad request / CSRF failure error template
│   ├── 404.html               # Resource not found error template
│   └── 500.html               # Server error template
│
└── tests/
    ├── __init__.py            # Test package initializer
    └── test_app.py            # Automated test suite (25 comprehensive tests)
```

---

## 6. Installation & Configuration

### Prerequisites
- Windows 11 / Windows 10
- Python 3.10+ (Current: Python 3.14.6)
- MySQL Server 8.0+ running on port `3306`

### Step 1: Open Terminal in Project Directory
Open **Windows PowerShell** and navigate to `D:\HMS`:
```powershell
cd D:\HMS
```

### Step 2: Install Required Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Configure Database Credentials
Ensure your local `.env` file in `D:\HMS` is populated:
```ini
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=hospital_management

# Flask Configuration
SECRET_KEY=carepoint_hms_super_secret_session_key_2026
FLASK_DEBUG=False
PORT=5000
```

### Step 4: Verify Database & Users Table
Initialize the `users` table if not already present:
```powershell
python -c "import database; database.init_users_table(); print('Database ready!')"
```

### Step 5: Provision the Initial Administrator Account
Use the dedicated CLI script to create an administrator account (or use interactive prompts):
```powershell
python create_admin.py --name "Dr. Sharma" --email "admin@carepoint.health" --password "Admin@CarePoint2026" --role "Administrator"
```

---

## 7. How to Run the Application

Start the Flask server using Python:

```powershell
python app.py
```

The console will output:
```
Starting CarePoint Hospital Management System on http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Open your browser to:
- **Public Landing Page**: 👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**
- **Staff Registration**: 👉 **[http://127.0.0.1:5000/signup](http://127.0.0.1:5000/signup)**
- **Staff Login**: 👉 **[http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)**
  - Default Demo Login: `admin@carepoint.health`
  - Default Demo Password: `Admin@CarePoint2026`
- **Authenticated Dashboard**: 👉 **[http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)**
- **User Governance (Admin)**: 👉 **[http://127.0.0.1:5000/admin/users](http://127.0.0.1:5000/admin/users)**

---

## 8. Running Automated Tests

The application includes an automated test suite verifying database connectivity, authentication, session lifecycle, staff signup, pending status enforcement, administrative approval workflows, all clinical/operational modules, form validation, CSRF defense, and safe deletion integrity.

Run the test suite using `pytest`:
```powershell
python -m pytest tests/test_app.py -v
```

All 25 test cases execute and pass:
```
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

============================= 25 passed in 23.28s =============================
```

---

## 9. Academic Documentation Suite

For detailed documentation, diagrams, and project reports, navigate to the `documentation/` folder:
- **[Documentation Index](documentation/README.md)**
- **[Project Overview & SRS](documentation/PROJECT_OVERVIEW.md)**
- **[Entity-Relationship Diagram & Modeling](documentation/ER_DIAGRAM.md)**
- **[Data Flow Diagrams (Level 0 & 1)](documentation/DATA_FLOW_DIAGRAMS.md)**
- **[System Flowchart](documentation/SYSTEM_FLOWCHART.md)**
- **[UML Use Case Documentation](documentation/USE_CASE_DIAGRAM.md)**
- **[Database Documentation & Data Dictionary](documentation/DATABASE_DOCUMENTATION.md)**
- **[Testing Documentation & Results](documentation/TESTING_DOCUMENTATION.md)**
- **[Full Academic Project Report](documentation/PROJECT_REPORT.md)**

---

## 10. Authors & License

- **Project**: CarePoint Hospital Management System (HMS)
- **Academic Purpose**: College DBMS Mini-Project (B.Tech CSE)
- **License**: Academic & Educational Use
