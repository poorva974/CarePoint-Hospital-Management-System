-- =============================================================================
-- CarePoint Hospital Management System (HMS)
-- Comprehensive DBMS Demonstration Queries & Concepts Reference
-- Target Database: MySQL (hospital_management)
-- =============================================================================

-- =============================================================================
-- SECTION 1: RELATIONAL SCHEMA DEFINITION (DDL)
-- =============================================================================
-- The database schema consists of 5 core relational entities enforcing
-- Primary Keys, Foreign Keys, Referential Integrity, and Data Typing.

/*
-- 1. Patient Entity
CREATE TABLE IF NOT EXISTS patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    dob DATE,
    phone VARCHAR(15),
    address VARCHAR(255)
);

-- 2. Doctor Entity
CREATE TABLE IF NOT EXISTS doctor (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    department VARCHAR(100)
);

-- 3. Appointment Entity (Child of patient & doctor)
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    time_slot VARCHAR(30),
    status VARCHAR(30) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
);

-- 4. Medical Record Entity (Child of patient, doctor & appointment)
CREATE TABLE IF NOT EXISTS medical_record (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT NOT NULL,
    diagnosis TEXT,
    prescription TEXT,
    report TEXT,
    record_date DATE DEFAULT (CURDATE()),
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
    FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id)
);

-- 5. Billing Entity (Child of patient & appointment)
CREATE TABLE IF NOT EXISTS billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appointment_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(30) DEFAULT 'Pending',
    insurance_details TEXT,
    bill_date DATE DEFAULT (CURDATE()),
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id)
);

-- 6. Users Entity (Authentication & Role-Based Access Control)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'Staff',
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
*/


-- =============================================================================
-- SECTION 2: BASIC CRUD OPERATIONS (DML)
-- =============================================================================

-- [CREATE / INSERT] Inserting a new patient
-- Concept: Column specification and value insertion
INSERT INTO patient (name, gender, dob, phone, address)
VALUES ('Kavita Nair', 'Female', '1996-04-12', '9876500006', 'Sector 62, Noida');

-- [CREATE / INSERT] Inserting a new doctor
INSERT INTO doctor (name, specialization, phone, email, department)
VALUES ('Dr. Sunita Rao', 'Dermatologist', '9876510006', 'sunita.rao@carepoint.health', 'Dermatology');

-- [READ / SELECT] Selecting all patients
SELECT patient_id, name, gender, dob, phone, address 
FROM patient 
ORDER BY patient_id DESC;

-- [READ / SELECT with WHERE] Finding a doctor by specialization
SELECT doctor_id, name, department, phone 
FROM doctor 
WHERE specialization = 'Cardiologist';

-- [UPDATE] Updating patient phone and address
UPDATE patient 
SET phone = '9876509999', address = 'Indirapuram, Ghaziabad'
WHERE patient_id = 1;

-- [UPDATE] Updating appointment status
UPDATE appointment
SET status = 'Completed'
WHERE appointment_id = 1;

-- [DELETE] Deleting a record safely (only if no foreign key references exist)
-- DELETE FROM billing WHERE bill_id = 999;


-- =============================================================================
-- SECTION 3: RELATIONAL JOINS (INNER JOIN & MULTI-TABLE JOINS)
-- =============================================================================

-- Query 1: 3-Table INNER JOIN to display complete appointment schedule
-- Combines appointment, patient, and doctor records using foreign keys
SELECT 
    a.appointment_id,
    a.appointment_date,
    a.time_slot,
    a.status,
    p.patient_id,
    p.name AS patient_name,
    p.phone AS patient_phone,
    d.doctor_id,
    d.name AS doctor_name,
    d.department,
    d.specialization
FROM appointment a
INNER JOIN patient p ON a.patient_id = p.patient_id
INNER JOIN doctor d ON a.doctor_id = d.doctor_id
ORDER BY a.appointment_date DESC, a.time_slot ASC;

-- Query 2: 4-Table INNER JOIN for Medical Record Clinical Audit
-- Relates medical diagnosis with patient info, attending physician, and consultation date
SELECT 
    m.record_id,
    m.record_date,
    p.name AS patient_name,
    p.gender,
    d.name AS doctor_name,
    d.department,
    a.time_slot,
    m.diagnosis,
    m.prescription,
    m.report
FROM medical_record m
INNER JOIN patient p ON m.patient_id = p.patient_id
INNER JOIN doctor d ON m.doctor_id = d.doctor_id
INNER JOIN appointment a ON m.appointment_id = a.appointment_id
ORDER BY m.record_date DESC;

-- Query 3: Multi-Table JOIN for Billing and Revenue Ledger
-- Shows invoice amount, payment status, patient name, and doctor
SELECT 
    b.bill_id,
    b.bill_date,
    p.name AS patient_name,
    d.name AS doctor_name,
    d.department,
    b.amount,
    b.payment_status,
    b.insurance_details
FROM billing b
INNER JOIN patient p ON b.patient_id = p.patient_id
INNER JOIN appointment a ON b.appointment_id = a.appointment_id
INNER JOIN doctor d ON a.doctor_id = d.doctor_id
ORDER BY b.bill_date DESC;


-- =============================================================================
-- SECTION 4: OUTER JOINS (LEFT JOIN)
-- =============================================================================

-- Query 4: Doctors and their total booked consultations
-- Demonstrates LEFT JOIN so doctors with ZERO appointments are still included
SELECT 
    d.doctor_id,
    d.name AS doctor_name,
    d.specialization,
    d.department,
    COUNT(a.appointment_id) AS total_appointments_booked
FROM doctor d
LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, d.name, d.specialization, d.department
ORDER BY total_appointments_booked DESC;

-- Query 5: Identifying Patients who have NEVER booked an appointment
-- Concept: Unmatched rows detection in relational algebra
SELECT 
    p.patient_id,
    p.name AS patient_name,
    p.phone
FROM patient p
LEFT JOIN appointment a ON p.patient_id = a.patient_id
WHERE a.appointment_id IS NULL;


-- =============================================================================
-- SECTION 5: AGGREGATE FUNCTIONS & GROUP BY ANALYTICS
-- =============================================================================

-- Query 6: Hospital Financial Metrics (SUM, COUNT, AVG, MIN, MAX)
SELECT 
    COUNT(*) AS total_invoices_issued,
    SUM(amount) AS total_billed_amount,
    AVG(amount) AS average_bill_amount,
    MIN(amount) AS lowest_bill_amount,
    MAX(amount) AS highest_bill_amount
FROM billing;

-- Query 7: Revenue Breakdown by Payment Status (GROUP BY)
SELECT 
    payment_status,
    COUNT(*) AS invoice_count,
    SUM(amount) AS total_amount,
    ROUND(AVG(amount), 2) AS average_amount
FROM billing
GROUP BY payment_status
ORDER BY total_amount DESC;

-- Query 8: Departmental Workload & Distribution (GROUP BY on JOIN)
SELECT 
    d.department,
    COUNT(DISTINCT d.doctor_id) AS active_doctors,
    COUNT(a.appointment_id) AS total_appointments
FROM doctor d
LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.department
ORDER BY total_appointments DESC;

-- Query 9: High-Volume Doctors (GROUP BY with HAVING Clause)
-- Demonstrates filtering aggregated groups (HAVING COUNT >= 1)
SELECT 
    d.doctor_id,
    d.name AS doctor_name,
    d.department,
    COUNT(a.appointment_id) AS appointment_count
FROM doctor d
INNER JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, d.name, d.department
HAVING COUNT(a.appointment_id) >= 1
ORDER BY appointment_count DESC;


-- =============================================================================
-- SECTION 6: SUBQUERIES & ADVANCED RELATIONAL FILTERING
-- =============================================================================

-- Query 10: Invoices that exceed the average hospital bill (Scalar Subquery)
SELECT 
    b.bill_id,
    p.name AS patient_name,
    b.amount,
    b.payment_status
FROM billing b
INNER JOIN patient p ON b.patient_id = p.patient_id
WHERE b.amount > (SELECT AVG(amount) FROM billing)
ORDER BY b.amount DESC;

-- Query 11: Doctors who have treated patients with 'hypertension' (Correlated Subquery / IN)
SELECT doctor_id, name, specialization, department
FROM doctor
WHERE doctor_id IN (
    SELECT DISTINCT doctor_id 
    FROM medical_record 
    WHERE diagnosis LIKE '%hypertension%'
);


-- =============================================================================
-- SECTION 7: REFERENTIAL INTEGRITY & PRE-DELETION VERIFICATION
-- =============================================================================

-- Query 12: Checking for dependent child records before attempting to delete a patient
-- In our application, this check prevents MySQL Foreign Key Constraint Error #1451
SELECT 
    (SELECT COUNT(*) FROM appointment WHERE patient_id = 1) AS dependent_appointments,
    (SELECT COUNT(*) FROM medical_record WHERE patient_id = 1) AS dependent_medical_records,
    (SELECT COUNT(*) FROM billing WHERE patient_id = 1) AS dependent_bills;


-- =============================================================================
-- SECTION 8: DATABASE TRANSACTIONS (ACID PROPERTIES DEMONSTRATION)
-- =============================================================================

-- Demonstration of an Atomic Transaction (BEGIN, COMMIT, ROLLBACK)
-- When a doctor consultation is finalized and an invoice is simultaneously generated:

START TRANSACTION;

-- Step 1: Mark appointment as Completed
UPDATE appointment 
SET status = 'Completed' 
WHERE appointment_id = 1;

-- Step 2: Add Medical Record
INSERT INTO medical_record (patient_id, doctor_id, appointment_id, diagnosis, prescription, report, record_date)
VALUES (1, 1, 1, 'Routine follow-up completed. Normal blood pressure.', 'Continue current regimen', 'Vitals normal', CURDATE());

-- Step 3: Insert or update bill
-- If all statements succeed without error, finalize the transaction:
COMMIT;

-- In case of failure or constraint conflict:
-- ROLLBACK;


-- =============================================================================
-- SECTION 9: USER AUTHENTICATION & ACCESS GOVERNANCE QUERIES
-- =============================================================================

-- Query 13: Staff Registration with Pending Status (Public /signup)
-- Enforces password hashing at application layer; role strictly 'Staff'
INSERT INTO users (name, email, password_hash, role, status)
VALUES ('Nurse Sunita Rao', 'sunita.rao@carepoint.health', 'scrypt:32768:8:1$examplehash...', 'Staff', 'Pending');

-- Query 14: Inspecting Pending Registration Requests (Admin Review)
SELECT user_id, name, email, role, status, created_at 
FROM users 
WHERE status = 'Pending'
ORDER BY created_at ASC;

-- Query 15: Administrator Approves a Staff Account
UPDATE users 
SET status = 'Approved' 
WHERE user_id = 2;

-- Query 16: Authentication Lookup by Normalized Email (Login)
SELECT user_id, name, email, password_hash, role, status 
FROM users 
WHERE email = 'admin@carepoint.health';

-- Query 17: Administrative Safety Check (Count of other active administrators)
-- Ensures an administrator cannot delete or demote themselves if they are the sole admin
SELECT COUNT(*) AS active_admin_count 
FROM users 
WHERE role = 'Administrator' AND status = 'Approved' AND user_id != 1;


