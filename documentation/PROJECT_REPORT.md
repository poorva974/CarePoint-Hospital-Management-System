# Academic Project Report

# CAREPOINT: HOSPITAL MANAGEMENT SYSTEM
### A Relational Database Management System (DBMS) Mini-Project
**Bachelor of Technology in Computer Science & Engineering**

---

## Abstract

Healthcare institutions face substantial operational challenges when managing patient health records, physician availability schedules, clinical consultation encounters, diagnostic test summaries, and billing workflows using disparate or legacy manual methods. This project presents **CarePoint**, a full-stack, relational database-driven **Hospital Management System (HMS)** designed and implemented to provide centralized, secure, and intuitive administration for hospital operations.

CarePoint is engineered using a three-tier architecture comprising a modern HTML5/CSS3/JavaScript frontend, a Python Flask microframework application tier, and an enterprise-grade MySQL relational database storage engine (`hospital_management`). The database model incorporates six relational entities (`patient`, `doctor`, `appointment`, `medical_record`, `billing`, and `users`), adhering strictly to Third Normal Form (3NF) and Boyce-Codd Normal Form (BCNF) principles. Referential integrity is strictly maintained through foreign key constraints, while the application layer prevents cascade crashes with proactive dependency checks. 

Security is integrated at every architectural boundary: a public landing page introduces hospital services, public staff registration (`/signup`) captures pending employee profiles, and administrative staff governance (`/admin/users`) regulates user access with approval workflows. All administrative and clinical modules require authenticated session authorization backed by salted `scrypt` cryptographic password hashing, Cross-Site Request Forgery (CSRF) protection, and parameterized SQL queries to mitigate SQL injection vulnerabilities. A comprehensive automated test suite consisting of 25 test cases demonstrates 100% test pass rates across functional, security, administrative approval, and relational integrity dimensions.

---

## Table of Contents

1. [Chapter 1: Introduction](#chapter-1-introduction)
   - 1.1 Project Background
   - 1.2 Problem Statement
   - 1.3 Project Objectives
   - 1.4 Scope and Limitations
2. [Chapter 2: System Analysis & Architecture](#chapter-2-system-analysis--architecture)
   - 2.1 Existing System Analysis
   - 2.2 Proposed System Architecture
   - 2.3 Feasibility Analysis
3. [Chapter 3: Software Requirements Specification](#chapter-3-software-requirements-specification)
   - 3.1 Functional Requirements
   - 3.2 Non-Functional Requirements
   - 3.3 Hardware & Software Specifications
4. [Chapter 4: System Design & Modeling](#chapter-4-system-design--modeling)
   - 4.1 Entity-Relationship (ER) Model
   - 4.2 Data Flow Diagrams (DFD Level 0 and Level 1)
   - 4.3 System Flowchart
   - 4.4 UML Use Case Diagram
5. [Chapter 5: Relational Database Design](#chapter-5-relational-database-design)
   - 5.1 Database Schema & Data Dictionary
   - 5.2 Normalization Analysis (1NF, 2NF, 3NF, BCNF)
   - 5.3 Referential Integrity & Cascade Safety
   - 5.4 Demonstration SQL Queries (CRUD, JOINs, Aggregates)
6. [Chapter 6: Implementation & Security](#chapter-6-implementation--security)
   - 6.1 Backend Implementation (Flask & MySQL Connector)
   - 6.2 Authentication & Session Architecture
   - 6.3 Secure Administrative Account Provisioning
   - 6.4 Frontend Design & Responsive UI
7. [Chapter 7: Testing & Verification](#chapter-7-testing--verification)
   - 7.1 Testing Strategy
   - 7.2 Test Cases & Execution Matrix
   - 7.3 Security Audit Results
8. [Chapter 8: Conclusion & Future Scope](#chapter-8-conclusion--future-scope)
   - 8.1 Summary of Contributions
   - 8.2 Future Enhancements
9. [References](#references)

---

## Chapter 1: Introduction

### 1.1 Project Background
In modern clinical care, timely access to patient history, medical diagnoses, doctor scheduling, and invoicing records directly impacts patient outcomes and institutional efficiency. The CarePoint Hospital Management System is developed as an academic DBMS mini-project to demonstrate the practical application of relational database concepts, relational algebra, SQL optimization, and web application security in a real-world healthcare scenario.

### 1.2 Problem Statement
Traditional paper-based records and fragmented spreadsheet systems suffer from significant vulnerabilities:
- High data redundancy leading to update and deletion anomalies.
- Lack of referential integrity enforcement, allowing orphaned appointment or billing records.
- Inadequate access controls, exposing sensitive clinical information.
- Inefficient search and query performance during emergencies.
- Absence of centralized billing reconciliation linked to clinical consultations.

### 1.3 Project Objectives
The primary objectives of CarePoint are:
1. **Relational Integrity**: Construct a robust MySQL schema enforcing primary keys, foreign keys, and domain constraints across six core tables.
2. **Centralized Management**: Provide comprehensive Create, Read, Update, and Delete (CRUD) modules for patients, doctors, appointments, medical records, and billing.
3. **End-to-End Security**: Implement secure user authentication using salted `scrypt` hashing, session token management, route guards, and CSRF protection.
4. **Intuitive Presentation**: Deliver a responsive web interface featuring a public landing page, clean login modal, dynamic KPI metrics dashboard, and accessible management interfaces.
5. **Practical DBMS Demonstration**: Showcase multi-table `INNER JOIN` operations, aggregate statistical analytics (`SUM`, `COUNT`, `AVG`), and transactional consistency.

### 1.4 Scope and Limitations
- **Scope**: Covers internal hospital outpatient administration, patient registration, physician scheduling, electronic medical record authoring, bill creation, payment tracking, and user account management.
- **Limitations**: Inpatient ward bed allocation, pharmacy inventory stock control, and automated external credit card processing gateways are outside the initial mini-project scope.

---

## Chapter 2: System Analysis & Architecture

### 2.1 Existing System Analysis
In the legacy operational model, patient files are physically retrieved from medical record rooms. Appointments are manually recorded in physical registers, leading to double-booking of doctor slots, unrecorded prescription changes, and billing discrepancies. Retrieving historical diagnoses requires significant manual effort, creating operational bottlenecks.

### 2.2 Proposed System Architecture
CarePoint employs a **Three-Tier Client-Server Architecture**:
1. **Presentation Tier (Client)**: Modern HTML5, CSS3, JavaScript, and Jinja2 templates providing accessible UI components, form validation, dynamic modals, and responsive layout.
2. **Application Tier (Backend)**: Python 3.14 running Flask, handling HTTP routing, session management, CSRF validation, parameter sanitization, and business logic.
3. **Data Tier (Database)**: MySQL 8.0 server with `InnoDB` storage engine, executing parameterized SQL queries, enforcing ACID properties, foreign key constraints, and indexing.

```
+-------------------------------------------------------------------------+
|                          THREE-TIER ARCHITECTURE                        |
+-------------------------------------------------------------------------+
|  PRESENTATION TIER  | Web Browser (HTML5 / CSS3 / JavaScript / Jinja2)  |
|         |           | Public Landing, Login, Dashboard, Management UIs  |
+---------|---------------------------------------------------------------+
|         v                                                               |
|  APPLICATION TIER   | Python Flask Application Server (app.py)          |
|         |           | Route Interceptors, @login_required, CSRF, Hashing|
+---------|---------------------------------------------------------------+
|         v                                                               |
|  DATA STORAGE TIER  | MySQL 8.0 DBMS (hospital_management)              |
|                     | InnoDB Engine: patient, doctor, appointment, etc. |
+-------------------------------------------------------------------------+
```

### 2.3 Feasibility Analysis
- **Technical Feasibility**: Built with established open-source tools (Python, Flask, MySQL) requiring no proprietary licenses. Compatible with standard OS platforms (Windows, Linux, macOS).
- **Economic Feasibility**: Zero software licensing cost; lightweight infrastructure footprint suitable for deployment on standard institutional hardware.
- **Operational Feasibility**: Minimal training required for hospital staff due to clear UI labels, intuitive color indicators, and automated error prevention.

---

## Chapter 3: Software Requirements Specification

### 3.1 Functional Requirements
- **FR-01 (Public Portal)**: Provide a clean landing page at `/` detailing hospital capabilities without exposing patient data.
- **FR-02 (Secure Authentication)**: Validate staff login at `/login` with `scrypt` password verification; maintain authenticated sessions with secure cookies.
- **FR-03 (Route Protection)**: Restrict access to `/dashboard` and all management modules to authenticated users; redirect anonymous requests to `/login?next=...`.
- **FR-04 (Dashboard Analytics)**: Display real-time KPI metrics (Total Patients, Doctors, Scheduled Appointments, Paid Revenue) and top 5 recent consultations.
- **FR-05 (Patient Management)**: Support registration, editing, search, and safe deletion of patient records.
- **FR-06 (Doctor Directory)**: Display clinical staff categorized by specialty, department, and contact information.
- **FR-07 (Appointment Scheduling)**: Create and update consultation appointments with status transitions (`Scheduled`, `Completed`, `Cancelled`).
- **FR-08 (Medical Records)**: Link diagnoses, prescriptions, and lab reports with patient, doctor, and appointment keys.
- **FR-09 (Billing Management)**: Generate itemized invoices; track payment status (`Pending`, `Paid`) and insurance references.
- **FR-10 (Session Termination)**: Invalidate server-side session and client cookie upon `/logout`.
- **FR-11 (Administrative Provisioning)**: Provide CLI script `create_admin.py` to create admin accounts with hashed credentials.

### 3.2 Non-Functional Requirements
- **Security**: Strong password hashing (`scrypt`), CSRF token validation on all POST requests, parameterized SQL queries preventing SQL injection, open redirect protection.
- **Performance**: Sub-100ms response times for typical database queries via indexed foreign and primary keys.
- **Reliability & ACID Compliance**: InnoDB storage engine guarantees Atomicity, Consistency, Isolation, and Durability.
- **Usability**: Responsive design adapted for desktops, laptops, tablets, and smartphones.

### 3.3 Hardware & Software Specifications
- **Hardware**: Intel/AMD x86-64 CPU (2.0 GHz+), 4 GB RAM minimum, 500 MB disk space.
- **Software**: Windows 11 / Linux Ubuntu 22.04+, Python 3.10+ (tested on Python 3.14.6), MySQL Server 8.0+, Google Chrome / Mozilla Firefox / Microsoft Edge.

---

## Chapter 4: System Design & Modeling

### 4.1 Entity-Relationship (ER) Model
The relational schema comprises six entities. The diagram below illustrates entities, attributes, primary keys, and cardinality constraints:

- Detailed Documentation: [ER_DIAGRAM.md](ER_DIAGRAM.md)
- Vector Graphic: [er_diagram.svg](diagrams/er_diagram.svg)
- Mermaid Source: [er_diagram.mmd](diagrams/er_diagram.mmd)

```
[PATIENT] 1 ----< N [APPOINTMENT] N >---- 1 [DOCTOR]
    |                      |                    |
    | 1                    | 1                  | 1
    |                      |                    |
    +----< N [BILLING] >---+                    |
    |                      |                    |
    +----< N [MEDICAL_RECORD] >-----------------+
```

### 4.2 Data Flow Diagrams (DFD)
- **Context Level-0 DFD**: Illustrates external entities (Public Visitor, Staff/Doctor, Administrator, MySQL) interacting with the CarePoint system boundary.
  - Vector Graphic: [dfd_level0.svg](diagrams/dfd_level0.svg)
- **Detailed Level-1 DFD**: Deconstructs the system into sub-processes (1.0 Authentication, 2.0 Patient Care, 3.0 Clinical Appointments, 4.0 Medical Records, 5.0 Billing, 6.0 Analytics) and data stores (D1 to D6).
  - Vector Graphic: [dfd_level1.svg](diagrams/dfd_level1.svg)
  - Detailed Specification: [DATA_FLOW_DIAGRAMS.md](DATA_FLOW_DIAGRAMS.md)

### 4.3 System Flowchart
Depicts the logical decision pathways of the application, including unauthenticated redirect loops, login verification, dashboard rendering, module CRUD workflows, and session logout.
- Detailed Specification: [SYSTEM_FLOWCHART.md](SYSTEM_FLOWCHART.md)
- Vector Graphic: [system_flowchart.svg](diagrams/system_flowchart.svg)

### 4.4 UML Use Case Diagram
Models interactions between system actors (Public Visitor, Hospital Staff, Administrator) and functional use cases (UC-01 through UC-09).
- Detailed Specification: [USE_CASE_DIAGRAM.md](USE_CASE_DIAGRAM.md)
- Vector Graphic: [use_case_diagram.svg](diagrams/use_case_diagram.svg)

---

## Chapter 5: Relational Database Design

### 5.1 Database Schema & Data Dictionary
The database `hospital_management` incorporates six relational tables:

1. **`patient`** (`patient_id` [PK], `name`, `gender`, `dob`, `phone`, `address`)
2. **`doctor`** (`doctor_id` [PK], `name`, `specialization`, `phone`, `email`, `department`)
3. **`appointment`** (`appointment_id` [PK], `patient_id` [FK], `doctor_id` [FK], `appointment_date`, `time_slot`, `status`)
4. **`medical_record`** (`record_id` [PK], `patient_id` [FK], `doctor_id` [FK], `appointment_id` [FK], `diagnosis`, `prescription`, `report`, `record_date`)
5. **`billing`** (`bill_id` [PK], `patient_id` [FK], `appointment_id` [FK], `amount`, `payment_status`, `insurance_details`, `bill_date`)
6. **`users`** (`user_id` [PK], `name`, `email` [UNIQUE], `password_hash`, `role`, `status`, `created_at`)

*(For complete column types, constraints, and descriptions, see [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md).)*

### 5.2 Normalization Analysis
- **1NF**: All attributes contain atomic, scalar values; no repeating groups.
- **2NF**: All non-key attributes depend entirely on single-attribute surrogate primary keys; zero partial functional dependencies.
- **3NF**: Zero transitive dependencies; non-key attributes depend only on the primary key.
- **BCNF**: Every determinant in every non-trivial functional dependency is a superkey.

### 5.3 Referential Integrity & Cascade Safety
MySQL foreign keys are configured with `ON DELETE RESTRICT`. To prevent unhandled database exceptions (MySQL Error 1451), `app.py` implements proactive pre-delete integrity checks:
```python
cursor.execute("SELECT COUNT(*) AS total FROM appointment WHERE patient_id = %s", (patient_id,))
if cursor.fetchone()['total'] > 0:
    flash("Cannot delete patient: active appointment records exist.", "danger")
    return redirect(url_for('patients'))
```

### 5.4 Demonstration SQL Queries

#### Multi-Table INNER JOIN (Comprehensive Appointment Schedule):
```sql
SELECT 
    a.appointment_id,
    p.name AS patient_name,
    p.phone AS patient_phone,
    d.name AS doctor_name,
    d.department,
    a.appointment_date,
    a.time_slot,
    a.status
FROM appointment a
INNER JOIN patient p ON a.patient_id = p.patient_id
INNER JOIN doctor d ON a.doctor_id = d.doctor_id
ORDER BY a.appointment_date DESC;
```

#### Analytical KPI Aggregation:
```sql
SELECT 
    (SELECT COUNT(*) FROM patient) AS total_patients,
    (SELECT COUNT(*) FROM doctor) AS total_doctors,
    (SELECT COUNT(*) FROM appointment WHERE status = 'Scheduled') AS active_appointments,
    (SELECT COALESCE(SUM(amount), 0.00) FROM billing WHERE payment_status = 'Paid') AS total_revenue;
```

---

## Chapter 6: Implementation & Security

### 6.1 Backend Implementation
The backend application (`app.py`) is organized using Flask application design principles:
- **Database Connection Management**: `database.py` manages MySQL connections with automatic reconnection and dictionary cursors.
- **Parameterized Execution**: All SQL statements utilize `%s` parameter substitution, completely isolating user input from the SQL query syntax.

### 6.2 Authentication & Session Architecture
- **Route Guard Decorator**:
  ```python
  def login_required(f):
      @wraps(f)
      def decorated_function(*args, **kwargs):
          if "user_id" not in session:
              flash("Please log in to access this page.", "warning")
              return redirect(url_for("login", next=request.path))
          return f(*args, **kwargs)
      return decorated_function
  ```
- **Cryptographic Hashing**: Passwords are never stored in plaintext. Hashes are generated via `werkzeug.security.generate_password_hash(password, method='scrypt')`.
- **Timing-Attack Resistance**: Verification uses `check_password_hash`, comparing hashes in constant time.
- **Generic Error Messages**: Invalid credentials produce *"Invalid email or password."*, preventing user enumeration.

### 6.3 Secure Administrative Account Provisioning
A dedicated CLI script (`create_admin.py`) allows system operators to safely provision administrative credentials:
```bash
python create_admin.py --name "Dr. Sharma" --email "admin@carepoint.health" --password "Admin@CarePoint2026" --role "Administrator"
```

### 6.4 Frontend Design & Responsive UI
- **Branding**: CarePoint design language utilizing deep navy blue (`#0f172a`), clinical blue (`#0284c7`), and clear status indicators.
- **Components**: Responsive data tables with search filters, dynamic modal dialogs for record creation/editing, and status badges (`Paid`, `Pending`, `Scheduled`, `Completed`).

---

## Chapter 7: Testing & Verification

### 7.1 Testing Strategy
The system underwent testing across four dimensions:
1. **Unit Testing**: Isolated verification of hashing and parameter validation.
2. **Integration Testing**: Verification of database transactions and relational constraints against live MySQL.
3. **Security Testing**: Verification of route guards, CSRF rejection, and SQL injection resistance.
4. **Functional Testing**: End-to-end verification of user workflows.

### 7.2 Test Cases & Execution Matrix
All 25 automated tests in `tests/test_app.py` passed successfully:

| Test ID | Module | Purpose | Status |
| :---: | :--- | :--- | :--- | :---: |
| TC-01 | Database Connectivity | Live MySQL ping and schema verification | **PASS** |
| TC-02 | Public Landing | Renders `/` without exposing private clinical data | **PASS** |
| TC-03 | Authorization Guard | `/dashboard` redirects unauthenticated users | **PASS** |
| TC-04 | Login Validation | Invalid password rejected with generic alert | **PASS** |
| TC-05 | Login & Open Redirect | Valid login establishes session and prevents open redirect | **PASS** |
| TC-06 | Dashboard Analytics | Authenticated user views live aggregate KPIs and data | **PASS** |
| TC-07 | Session Management | `/logout` invalidates session and redirects to landing | **PASS** |
| TC-08 | Patient Management | Authenticated list, filtering, and search | **PASS** |
| TC-09 | Patient Detail View | Relational appointment and billing history rendering | **PASS** |
| TC-10 | Doctor Directory | Departmental filtering, specialty tracking, and directory | **PASS** |
| TC-11 | Appointment Scheduling | Conflict-free appointment creation with foreign key checks | **PASS** |
| TC-12 | Medical Records | Clinical diagnosis charting linked to appointment | **PASS** |
| TC-13 | Billing & Invoicing | Itemized invoice creation and receipt view | **PASS** |
| TC-14 | Form Validation | Input sanitization, negative fee and duplicate slot blocking | **PASS** |
| TC-15 | Referential Integrity | Restricts deleting patients/doctors with child records | **PASS** |
| TC-16 | Safe CRUD Lifecycle | End-to-end creation, modification, and deletion of isolated test entity | **PASS** |
| TC-17 | CSRF Protection | Rejects unauthorized state-changing POST requests | **PASS** |
| TC-18 | Error Handling | Custom 404 page rendering for invalid routes | **PASS** |
| TC-19 | Staff Self-Registration | Public `/signup` captures staff with status `Pending` | **PASS** |
| TC-20 | Signup Validation | Rejects weak passwords (<8 chars) and duplicate emails (HTTP 409) | **PASS** |
| TC-21 | Status Enforcement | Blocks `Pending`, `Rejected`, or `Disabled` staff from logging in | **PASS** |
| TC-22 | Admin User Portal | Administrator approves/rejects staff and updates status | **PASS** |
| TC-23 | Post-Approval Login | Approved staff successfully authenticates and accesses dashboard | **PASS** |
| TC-24 | Role Isolation | Staff accounts receive HTTP 403 / redirect when accessing `/admin/users` | **PASS** |
| TC-25 | Admin Invariants | System strictly prevents self-deletion and demotion of the sole administrator | **PASS** |

*(For full execution logs and details, refer to [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md).)*

---

## Chapter 8: Conclusion & Future Scope

### 8.1 Summary of Contributions
CarePoint demonstrates that a robust, professional, and secure Hospital Management System can be implemented using standard relational database techniques and lightweight full-stack Python technologies:
- Preserved existing database schema while seamlessly adding a dedicated `users` authentication table with account status lifecycle management (`Pending`, `Approved`, `Rejected`, `Disabled`).
- Implemented real authentication with salted `scrypt` hashing, CSRF protection, and two-tier staff registration/administrative approval workflows.
- Protected all operational hospital modules behind secure session guards, with dedicated administrative role isolation for `/admin/users`.
- Achieved 100% test pass rate across 25 automated test cases in `pytest`.
- Generated comprehensive academic documentation including ER diagrams, DFDs, Flowcharts, Use Cases, and Data Dictionaries.

### 8.2 Future Enhancements
Potential extensions for future iterations:
1. **Granular Role-Based Access Control (RBAC)**: Fine-grained permissions differentiating Doctors (read/write medical records), Receptionists (appointments/patients), and Billing Clerks.
2. **Automated Notification Engine**: SMS and email appointment reminders via Twilio or SendGrid APIs.
3. **Automated PDF Export**: Server-side PDF invoice and clinical report generation using WeasyPrint or ReportLab.
4. **Electronic Health Records (EHR) Standards**: Integration with HL7/FHIR healthcare interoperability standards.

---

## References

1. **Silberschatz, A., Korth, H. F., & Sudarshan, S.** (2020). *Database System Concepts* (7th ed.). McGraw-Hill Education.
2. **Elmasri, R., & Navathe, S. B.** (2016). *Fundamentals of Database Systems* (7th ed.). Pearson.
3. **Grinberg, M.** (2018). *Flask Web Development: Developing Web Applications with Python* (2nd ed.). O'Reilly Media.
4. **MySQL 8.0 Reference Manual**. Oracle Corporation. Available at: https://dev.mysql.com/doc/refman/8.0/en/
5. **Werkzeug Password Security Documentation**. Pallets Projects. Available at: https://palletsprojects.com/p/werkzeug/
6. **OWASP Foundation**. *OWASP Top 10 Web Application Security Risks*. Available at: https://owasp.org/www-project-top-ten/

