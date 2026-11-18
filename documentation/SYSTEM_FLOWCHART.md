# System Flowchart & Application Execution Lifecycle
## CarePoint Hospital Management System (HMS)

---

### 1. Architectural Flowchart Description
The CarePoint application enforces a deterministic execution sequence governing initial public discovery, credential authentication, session regeneration, role-based dashboard access, transactional module execution, and secure session invalidation.

- **Vector Diagram**: [system_flowchart.svg](diagrams/system_flowchart.svg)

```
       [ START ]
           |
           v
    Landing Page ("/")
           |
           v
    Login Page ("/login")
           |
           v
  { Credentials Valid? }
      /           \
   [NO]           [YES]
    /               \
(Flash Error)        v
  |            Regenerate Session
  +---> Retry        |
                     v
             Dashboard ("/dashboard") <----+
                     |                     |
                     v                     |
            Select Module                  |
            (Patients, Doctors,            | (Continue)
             Appointments, EHR, Billing)   |
                     |                     |
                     v                     |
            Database Operation             |
            (CRUD / JOIN / Aggregate)      |
                     |                     |
                     v                     |
            Flash Feedback & PRG           |
                     |                     |
                     v                     |
             { Session Logout? } ----------+
                     |
                   [YES]
                     |
                     v
             Invalidate Session
                     |
                     v
                  [ END ]
```

---

### 2. Step-by-Step Execution Sequence

#### Step 1: Public Entry via Landing Page (`/`)
- A visitor requests the root domain `http://127.0.0.1:5000/`.
- Flask routes the request to `landing()`.
- The public promotional landing page is rendered without querying sensitive patient data or private clinical tables.

#### Step 2: Authentication Invocation (`/login`)
- The visitor clicks "Get Started" or "Staff Login".
- The server presents the login form with email, password, and a cryptographic CSRF token.
- If an unauthenticated visitor attempts to access a protected URL (e.g. `/patients`), Flask's `@login_required` decorator intercepts the request and redirects them to `/login?next=%2Fpatients`.

#### Step 3: Credential Verification & Session Regeneration
- The operator enters their credentials and submits via HTTP `POST`.
- Flask verifies the CSRF token.
- `app.py` queries `users` by email and compares the stored hash using `werkzeug.security.check_password_hash`.
- **Invalid Credentials Path**:
  - If the email does not exist or password hash comparison fails, the server issues an HTTP 401 response and flashes: *"Invalid email address or password. Please verify your credentials."*
  - The user remains on `/login` to retry. No user-enumeration indicators are exposed.
- **Valid Credentials Path**:
  - `session.clear()` is called to destroy any existing session and regenerate a new session identifier (preventing session fixation attacks).
  - `session['user_id']`, `session['user_name']`, `session['user_role']`, and `session['user_email']` are stored in the signed cookie.
  - The user is redirected to their validated `next_url` (or `/dashboard` by default).

#### Step 4: Authenticated Dashboard Operations (`/dashboard`)
- The server validates the active session via `@login_required`.
- Aggregate SQL queries are executed against MySQL:
  - `SELECT COUNT(*) FROM patient`
  - `SELECT COUNT(*) FROM doctor`
  - `SELECT COUNT(*) FROM appointment`
  - `SELECT SUM(amount) FROM billing WHERE payment_status = 'Paid'`
  - 3-table `INNER JOIN` query fetching the 8 most recent appointments.
- The dashboard view is populated with real MySQL records.

#### Step 5: Module Execution & Database Transactions
- The staff member selects a management module (e.g., Book Appointment, Record Diagnosis, Generate Bill).
- All input fields are validated server-side.
- Parameterized SQL queries (`%s` placeholders) execute with automatic commit and rollback:
  - **Appointment Conflict Check**: Confirms the doctor has no other active appointments at that time.
  - **Medical Record Alignment Check**: Verifies the selected appointment matches the designated patient and doctor.
  - **Billing Check**: Verifies the selected appointment belongs to the specified patient.
  - **Safe Deletion Check**: Inspects child tables (`appointment`, `medical_record`, `billing`) before permitting a deletion, blocking deletion if foreign key dependencies exist.

#### Step 6: Post/Redirect/Get (PRG) Feedback
- Upon write completion, Flask issues a redirect response (`302`) accompanied by a contextual flash message (`success`, `warning`, `danger`).
- The browser performs a clean `GET` request, preventing accidental duplicate form resubmissions when refreshing.

#### Step 7: Session Termination & Logout (`/logout`)
- The user clicks the visible "Logout" button in the topbar or sidebar.
- `logout()` invokes `session.clear()`, wiping all authentication keys.
- The user is redirected to `/login` with an informational notice: *"You have been signed out of CarePoint."*
- Subsequent attempts to reach protected URLs trigger an immediate redirect back to the login screen.

