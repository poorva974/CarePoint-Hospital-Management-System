# Database Documentation & Data Dictionary

## CarePoint Hospital Management System

---

## 1. Database Environment Overview

- **Database Engine**: MySQL 8.0+ / Community Server
- **Database Name**: `hospital_management`
- **Default Storage Engine**: `InnoDB` (ACID compliant, row-level locking, foreign key enforcement)
- **Character Set**: `utf8mb4`
- **Collation**: `utf8mb4_unicode_ci` / `utf8mb4_general_ci`
- **Connection Port**: `localhost:3306`
- **Driver**: `mysql-connector-python`

---

## 2. Table Schemas & Data Dictionary

The CarePoint database comprises **six relational tables**: five primary operational domain tables (`patient`, `doctor`, `appointment`, `medical_record`, `billing`) and one system authentication table (`users`).

### 2.1 Table: `patient`
Stores master demographic and contact details for registered hospital patients.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `patient_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for each patient. |
| `name` | `VARCHAR(100)` | *None* | **NO** | *None* | Full legal name of the patient. |
| `gender` | `VARCHAR(20)` | Domain: `Male`, `Female`, `Other` | YES | `NULL` | Biological sex or gender identity. |
| `dob` | `DATE` | ISO format `YYYY-MM-DD` | YES | `NULL` | Patient date of birth. Used to derive current age. |
| `phone` | `VARCHAR(15)` | *None* | YES | `NULL` | Primary telephone contact number. |
| `address` | `VARCHAR(255)` | *None* | YES | `NULL` | Residential address or locality. |

---

### 2.2 Table: `doctor`
Maintains the medical directory of healthcare practitioners across hospital departments.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `doctor_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for each physician. |
| `name` | `VARCHAR(100)` | *None* | **NO** | *None* | Full professional name of the doctor (e.g. Dr. Rajesh Sharma). |
| `specialization` | `VARCHAR(100)` | *None* | YES | `NULL` | Medical specialty (e.g. Cardiology, Neurology). |
| `phone` | `VARCHAR(15)` | *None* | YES | `NULL` | Office or duty telephone number. |
| `email` | `VARCHAR(100)` | *None* | YES | `NULL` | Professional hospital email contact. |
| `department` | `VARCHAR(100)` | *None* | YES | `NULL` | Clinical department (e.g. Outpatient, Cardiology). |

---

### 2.3 Table: `appointment`
Tracks scheduled, completed, and cancelled clinical consultations between patients and doctors.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `appointment_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for each appointment. |
| `patient_id` | `INT` | `FOREIGN KEY` (`patient.patient_id`) | **NO** | *None* | Reference to the patient attending the consultation. |
| `doctor_id` | `INT` | `FOREIGN KEY` (`doctor.doctor_id`) | **NO** | *None* | Reference to the assigned attending physician. |
| `appointment_date`| `DATE` | ISO format `YYYY-MM-DD` | **NO** | *None* | Scheduled calendar date of the consultation. |
| `time_slot` | `VARCHAR(30)` | e.g. `09:30 AM - 10:00 AM` | YES | `NULL` | Allocated consultation time interval. |
| `status` | `VARCHAR(30)` | Domain: `Scheduled`, `Completed`, `Cancelled` | YES | `'Scheduled'` | Current operational state of the appointment. |

---

### 2.4 Table: `medical_record`
Contains clinical encounter summaries, diagnoses, prescriptions, and lab test reports.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `record_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for each clinical record. |
| `patient_id` | `INT` | `FOREIGN KEY` (`patient.patient_id`) | **NO** | *None* | Reference to the patient diagnosed. |
| `doctor_id` | `INT` | `FOREIGN KEY` (`doctor.doctor_id`) | **NO** | *None* | Reference to the consulting physician authoring notes. |
| `appointment_id` | `INT` | `FOREIGN KEY` (`appointment.appointment_id`) | **NO** | *None* | Associated appointment linking encounter timeline. |
| `diagnosis` | `TEXT` | *None* | YES | `NULL` | Clinical diagnosis or condition observed. |
| `prescription` | `TEXT` | *None* | YES | `NULL` | Medications, dosage instructions, and schedules. |
| `report` | `TEXT` | *None* | YES | `NULL` | Diagnostic test summaries or lab findings. |
| `record_date` | `DATE` | Current date | YES | `CURRENT_DATE` | Date when the clinical entry was authored. |

---

### 2.5 Table: `billing`
Manages patient invoices, consultation fees, payment states, and insurance claims.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `bill_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for each invoice. |
| `patient_id` | `INT` | `FOREIGN KEY` (`patient.patient_id`) | **NO** | *None* | Reference to the billed patient. |
| `appointment_id` | `INT` | `FOREIGN KEY` (`appointment.appointment_id`) | **NO** | *None* | Reference to the consultation that incurred charges. |
| `amount` | `DECIMAL(10,2)` | Non-negative numeric currency | **NO** | *None* | Total billable amount in currency units (INR/USD). |
| `payment_status` | `VARCHAR(30)` | Domain: `Paid`, `Pending`, `Refunded` | YES | `'Pending'` | Settlement status of the invoice. |
| `insurance_details`| `TEXT` | Provider / Policy # / Copay | YES | `NULL` | Insurance coverage details or policy identifier. |
| `bill_date` | `DATE` | Current date | YES | `CURRENT_DATE` | Invoicing date. |

---

### 2.6 Table: `users`
Dedicated authentication table introduced to safeguard system credentials independently from medical entities.

| Column Name | Data Type | Constraints | Nullable | Default | Description |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `user_id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | **NO** | *None* | Unique surrogate identifier for system accounts. |
| `name` | `VARCHAR(100)` | *None* | **NO** | *None* | Full display name of the administrative user. |
| `email` | `VARCHAR(100)` | `UNIQUE` | **NO** | *None* | Unique staff email used for system sign-in. |
| `password_hash` | `VARCHAR(255)` | Salted cryptographic digest | **NO** | *None* | Password hash generated via `scrypt`. |
| `role` | `VARCHAR(30)` | Domain: `Administrator`, `Staff` | **NO** | `'Staff'` | Access role for authorization enforcement. |
| `status` | `VARCHAR(30)` | Domain: `Approved`, `Pending`, `Rejected`, `Disabled` | **NO** | `'Pending'` | Account lifecycle state. Self-registrations require admin approval. |
| `created_at` | `TIMESTAMP` | Current timestamp | YES | `CURRENT_TIMESTAMP` | Account creation timestamp for audit logging. |

---

## 3. Referential Integrity & Foreign Key Mapping

MySQL InnoDB actively enforces referential integrity across the operational tables:

```
+-------------------------------------------------------------------------------+
|                             FOREIGN KEY RELATIONSHIPS                         |
+----------------------+--------------------+---------------------+-------------+
| Child Table          | Foreign Key Column | Parent Table        | Primary Key |
+----------------------+--------------------+---------------------+-------------+
| appointment          | patient_id         | patient             | patient_id  |
| appointment          | doctor_id          | doctor              | doctor_id   |
| medical_record       | patient_id         | patient             | patient_id  |
| medical_record       | doctor_id          | doctor              | doctor_id   |
| medical_record       | appointment_id     | appointment         | appointm... |
| billing              | patient_id         | patient             | patient_id  |
| billing              | appointment_id     | appointment         | appointm... |
+----------------------+--------------------+---------------------+-------------+
```

### Deletion Safety & Referential Actions
- Standard MySQL relational policy on child foreign keys is `ON DELETE RESTRICT` / `NO ACTION`.
- **Application Level Safeguard**: In `app.py`, before any `DELETE FROM patient` or `DELETE FROM doctor` query is executed, the backend proactively executes:
  ```sql
  SELECT COUNT(*) FROM appointment WHERE patient_id = %s;
  SELECT COUNT(*) FROM medical_record WHERE patient_id = %s;
  SELECT COUNT(*) FROM billing WHERE patient_id = %s;
  ```
  If any child records exist, the operation is blocked gracefully, notifying the operator rather than triggering an unhandled database exception (MySQL Error 1451).

---

## 4. Normalization Analysis (1NF to BCNF)

A rigorous database design must prevent insertion, deletion, and update anomalies. Below is the formal normalization proof:

### 4.1 First Normal Form (1NF)
- **Criteria**: All attributes must be atomic (no repeating groups, multi-valued attributes, or composite attributes).
- **Proof**:
  - In `patient`, `name`, `gender`, `dob`, `phone`, and `address` hold single atomic scalar values.
  - In `medical_record`, `prescription` and `diagnosis` are stored as monolithic text narratives for clinical notes without internal array structures.
  - Every table possesses an explicit primary key (`patient_id`, `doctor_id`, `appointment_id`, `record_id`, `bill_id`, `user_id`).
  - **Verdict**: The schema satisfies **1NF**.

### 4.2 Second Normal Form (2NF)
- **Criteria**: The relation must be in 1NF and every non-key attribute must be fully functionally dependent on the entire primary key (no partial dependencies).
- **Proof**:
  - All six tables use **single-attribute surrogate primary keys** (`INT AUTO_INCREMENT`).
  - Because no primary key is composite, a partial dependency on a subset of the candidate key is mathematically impossible.
  - **Verdict**: The schema satisfies **2NF**.

### 4.3 Third Normal Form (3NF)
- **Criteria**: The relation must be in 2NF and no non-prime attribute may be transitively dependent on the primary key ($X \rightarrow Y$ and $Y \rightarrow Z$).
- **Proof**:
  - In `appointment`: `appointment_date`, `time_slot`, `status` depend directly on `appointment_id`. Doctor name is not redundantly stored here; it is reached via `doctor_id`.
  - In `billing`: `amount`, `payment_status`, `bill_date` depend strictly on `bill_id`. Patient demographics are not duplicated; they reside in `patient`.
  - In `medical_record`: Diagnosis and clinical data depend directly on `record_id`.
  - **Verdict**: The schema satisfies **3NF**.

### 4.4 Boyce-Codd Normal Form (BCNF)
- **Criteria**: For every non-trivial functional dependency $X \rightarrow Y$, $X$ must be a superkey.
- **Proof**:
  - In `users`: `email` is `UNIQUE`, forming an alternative candidate key. Both `user_id \rightarrow (name, email, password_hash, role)` and `email \rightarrow (user_id, name, password_hash, role)` have determinants that are superkeys.
  - Across all other tables, every functional dependency has the table primary key as its determinant.
  - **Verdict**: The schema satisfies **BCNF**.

---

## 5. SQL Demonstration Query Catalog

Below are practical SQL queries implemented in the application and ideal for DBMS mini-project viva evaluations:

### 5.1 Basic CRUD Queries

#### Create (Patient Registration):
```sql
INSERT INTO patient (name, gender, dob, phone, address)
VALUES ('Aarav Patel', 'Male', '1992-06-14', '9876543210', '42 MG Road, Bangalore');
```

#### Read (Filter Doctors by Department):
```sql
SELECT doctor_id, name, specialization, phone, email, department
FROM doctor
WHERE department = 'Cardiology'
ORDER BY name ASC;
```

#### Update (Settling a Medical Bill):
```sql
UPDATE billing
SET payment_status = 'Paid'
WHERE bill_id = 104;
```

#### Delete (Safely removing a patient with no active records):
```sql
DELETE FROM patient
WHERE patient_id = 25;
```

---

### 5.2 Multi-Table Relational JOIN Queries

#### Three-Table INNER JOIN (Comprehensive Appointment Schedule):
Combines patient names, doctor details, and scheduled consultation slots:
```sql
SELECT 
    a.appointment_id,
    p.patient_id,
    p.name AS patient_name,
    p.phone AS patient_phone,
    d.doctor_id,
    d.name AS doctor_name,
    d.specialization,
    d.department,
    a.appointment_date,
    a.time_slot,
    a.status
FROM appointment a
INNER JOIN patient p ON a.patient_id = p.patient_id
INNER JOIN doctor d ON a.doctor_id = d.doctor_id
ORDER BY a.appointment_date DESC, a.time_slot ASC;
```

#### Four-Table Clinical Encounter Dossier:
Retrieves diagnosis, prescription, doctor credentials, and patient background for a complete medical record review:
```sql
SELECT 
    m.record_id,
    m.record_date,
    p.name AS patient_name,
    p.dob AS patient_dob,
    d.name AS consulting_doctor,
    d.specialization,
    a.appointment_date,
    m.diagnosis,
    m.prescription,
    m.report
FROM medical_record m
INNER JOIN patient p ON m.patient_id = p.patient_id
INNER JOIN doctor d ON m.doctor_id = d.doctor_id
INNER JOIN appointment a ON m.appointment_id = a.appointment_id
WHERE p.patient_id = 1
ORDER BY m.record_date DESC;
```

---

### 5.3 Aggregate & Analytics Queries

#### Dashboard Summary KPI Calculation:
Computes patient counts, doctor availability, active appointments, and gross collected revenue:
```sql
SELECT 
    (SELECT COUNT(*) FROM patient) AS total_patients,
    (SELECT COUNT(*) FROM doctor) AS total_doctors,
    (SELECT COUNT(*) FROM appointment WHERE status = 'Scheduled') AS active_appointments,
    (SELECT COALESCE(SUM(amount), 0.00) FROM billing WHERE payment_status = 'Paid') AS total_revenue;
```

#### Department-Wise Patient Load (GROUP BY with Aggregate):
```sql
SELECT 
    d.department,
    COUNT(a.appointment_id) AS total_consultations,
    COUNT(DISTINCT a.patient_id) AS unique_patients
FROM doctor d
LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.department
ORDER BY total_consultations DESC;
```

#### Unpaid Invoices Analysis with Patient Contacts:
```sql
SELECT 
    b.bill_id,
    p.name AS patient_name,
    p.phone AS patient_phone,
    b.amount,
    b.bill_date,
    DATEDIFF(CURRENT_DATE, b.bill_date) AS days_outstanding
FROM billing b
INNER JOIN patient p ON b.patient_id = p.patient_id
WHERE b.payment_status = 'Pending'
ORDER BY b.amount DESC;
```

