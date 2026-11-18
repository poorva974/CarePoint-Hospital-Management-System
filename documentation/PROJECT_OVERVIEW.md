# CarePoint Hospital Management System (HMS)
## College DBMS Mini-Project: Project Overview & Requirement Analysis

---

### 1. Abstract
The **CarePoint Hospital Management System (HMS)** is a comprehensive, full-stack database management application engineered to automate and streamline hospital operations. Designed for healthcare administrative staff and physicians, CarePoint integrates patient registration, doctor directory maintenance, conflict-free appointment scheduling, electronic medical records (EMR) charting, and billing revenue management. Built on **Python Flask**, **MySQL 8.0**, and **HTML5/CSS3/JavaScript**, the system demonstrates fundamental relational database concepts including Boyce-Codd / Third Normal Form (3NF) relational design, foreign key referential integrity constraints, multi-table `JOIN` operations, aggregate calculations, atomic database transactions (ACID properties), session-based user authentication with cryptographic password hashing (`scrypt`), and cross-site request forgery (CSRF) protection.

---

### 2. Problem Statement
Traditional paper-based hospital administration and ad-hoc spreadsheet tracking suffer from critical systemic deficiencies:
1. **Data Redundancy & Inconsistency**: Patient demographics and medical records are frequently duplicated across multiple paper files and disjointed registries, leading to conflicting records and transcription errors.
2. **Scheduling Conflicts**: Manual appointment booking often results in double-booking of specialist doctors, scheduling appointments in the past, or booking appointments for non-existent doctors.
3. **Absence of Referential Integrity**: Deleting a patient or doctor record in unconstrained systems causes orphan appointments, clinical notes, and billing records, rendering clinical audit trails useless.
4. **Slow Information Retrieval**: Retrieving a patient's historical diagnoses, past consultation dates, attending physicians, and unpaid invoices requires manual searches across multiple physical ledgers.
5. **Lack of Access Control**: Unauthenticated access to sensitive patient clinical diagnoses, prescriptions, and financial billing exposes hospitals to data privacy and security vulnerabilities.

---

### 3. Objectives
The core objectives of the CarePoint Hospital Management System are:
- **Centralize Hospital Data**: Unify patient demographics, doctor profiles, consultation schedules, medical records, and billing into a centralized MySQL relational database.
- **Enforce Referential Integrity**: Maintain strict foreign key constraints across relational entities, safely intercepting and explaining cascading deletions to prevent orphan data.
- **Prevent Double-Booking**: Automate appointment slot validation to guarantee that no doctor is scheduled for more than one consultation at the same date and time slot.
- **Ensure Clinical Consistency**: Enforce business logic ensuring clinical records and billing invoices reference valid, matching appointments and patients.
- **Demonstrate Relational DBMS Concepts**: Provide practical, demonstrable implementations of `INNER JOIN`, `LEFT JOIN`, `COUNT`, `SUM`, `AVG`, `GROUP BY`, and database transactions for college viva examination and project reports.
- **Secure System Access**: Enforce role-based authentication (Administrator and Staff) using secure password hashing and session tokens.

---

### 4. Scope
#### In-Scope:
- Public informative landing page highlighting system features, architecture, and institutional information.
- Secure user login with cryptographic password verification and session fixation prevention.
- Main administrative dashboard deriving live statistics and recent appointments using SQL aggregate functions and `JOIN`s.
- Full CRUD (Create, Read, Update, Delete) management for Patients, Doctors, Appointments, Medical Records, and Billing.
- Search and multi-criteria filtering across all five operational entities.
- Safe deletion guards checking dependent child foreign keys before permitting table mutations.
- Printable hospital invoice generation with printable CSS media rules.

#### Out-of-Scope (Future Enhancements):
- Direct integration with third-party real-world payment gateways (e.g., Razorpay, Stripe) — simulated as academic status workflows (Paid, Pending, Partially Paid).
- Integration with external laboratory diagnostic machinery via DICOM / HL7 protocols.
- Automated SMS / WhatsApp appointment reminders via telecommunication APIs.

---

### 5. Functional Requirements (FR)

| Requirement ID | Module | Functional Description |
|---|---|---|
| **FR-01** | Landing Page | The root URL (`/`) must display a public landing page with CarePoint branding, hero value proposition, module feature cards, institutional about section, and login call-to-action. |
| **FR-02** | Authentication | The `/login` endpoint must authenticate registered staff against the MySQL `users` table using `scrypt` password hashing. Invalid attempts must produce generic error messages. |
| **FR-03** | Route Protection | All management routes and the `/dashboard` must require active session authentication. Unauthenticated requests must be redirected to `/login?next=...`. |
| **FR-04** | Session Termination | The `/logout` endpoint must invalidate the server-side session and redirect the user back to the login page. |
| **FR-05** | Real-Time Dashboard | The dashboard must compute and display live database metrics: Total Patients, Active Doctors, Total Appointments, Paid Revenue, and Pending Revenue using SQL aggregates. |
| **FR-06** | Patient CRUD | Staff must be able to register patients, view complete demographic and clinical histories, search by name or phone, update contact info, and safely delete unreferenced patients. |
| **FR-07** | Doctor Directory | Staff must be able to add doctors, specify departments and specialties, update profiles, search by specialty/dept, and track booked appointments via `LEFT JOIN`. |
| **FR-08** | Appointment Scheduling | The system must allow booking appointments from populated MySQL dropdowns, reject past dates, and reject bookings conflicting with an active appointment for the same doctor and time slot. |
| **FR-09** | Medical Records | Staff must record diagnoses, prescriptions, and lab examination notes. The system must validate that the chosen appointment belongs to the selected patient and doctor. |
| **FR-10** | Billing & Invoicing | Staff must generate itemized invoices for completed appointments, validate that amounts are non-negative, track payment status (Paid, Pending, Partially Paid), and print receipts. |
| **FR-11** | Referential Guardrails | Pre-deletion verification must query child foreign keys (`appointment`, `medical_record`, `billing`) and block deletion if dependent rows exist, explaining the relational barrier. |
| **FR-12** | Staff Self-Registration | The public `/signup` endpoint must allow clinical and operational staff to register accounts, validating password strength (>=8 characters) and uniqueness, defaulting to `role='Staff'` and `status='Pending'`. |
| **FR-13** | Admin Account Governance | The `/admin/users` management portal must allow administrators to inspect pending accounts, approve or reject staff registrations, toggle roles, and manage active status, with safety invariants preventing self-deletion and sole administrator demotion. |

---

### 6. Non-Functional Requirements (NFR)

1. **Security**:
   - Passwords must be hashed using `werkzeug.security` (scrypt / pbkdf2 with salt). No plaintext passwords stored.
   - All SQL operations must use parameterized queries (`%s` placeholders) to prevent SQL Injection.
   - State-changing HTTP POST requests must validate session-bound CSRF tokens.
   - Session cookies must enforce `HttpOnly` and `SameSite=Lax`.
2. **Reliability & Consistency**:
   - Transactions must adhere to ACID principles, rolling back automatically on query or integrity failures.
3. **Usability & Responsiveness**:
   - The user interface must employ a modern healthcare design palette (navy blue `#0f172a`, primary blue `#2563eb`, clean slate background `#f8fafc`).
   - The web layout must be responsive across desktop laptops, tablets, and mobile devices with collapsible navigation.
4. **Maintainability**:
   - Code must be modularized into reusable database helpers (`database.py`), route controllers (`app.py`), and Jinja2 template components.

---

### 7. Hardware & Software Requirements

#### Software Environment:
- **Operating System**: Windows 11 / Windows 10 / Linux / macOS
- **Programming Language**: Python 3.10+ (Tested on Python 3.14.6)
- **Web Framework**: Flask 3.1.3
- **Relational Database Engine**: MySQL Server 8.0+ (Tested on MySQL 8.0.46)
- **Database Driver**: `mysql-connector-python` 9.7.0
- **Web Browser**: Google Chrome, Mozilla Firefox, Microsoft Edge, or Safari
- **Development Tooling**: Visual Studio Code, Git, Windows PowerShell

#### Hardware Requirements:
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher
- **RAM**: Minimum 4 GB (8 GB recommended)
- **Storage**: Minimum 500 MB free hard disk space for project files and MySQL tables
- **Network**: Localhost / Intranet connectivity (Port 5000 for Flask, Port 3306 for MySQL)

