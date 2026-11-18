# Data Flow Diagrams (DFD) — Level 0 & Level 1
## CarePoint Hospital Management System (HMS)

---

### 1. DFD Level 0: Context Diagram
The Level 0 context diagram models the overall system boundary of CarePoint, showing external actors and the foundational flow of information into and out of the centralized hospital database.

- **Diagram File**: [dfd_level0.svg](diagrams/dfd_level0.svg)

```
[ Hospital Staff / Admin ]
        |
        |  1. Login Credentials, Patient Info, Appt Bookings, Diagnoses, Bills
        v
+-------------------------------------------------------+
| 0.0 CarePoint Hospital Management System              |
+-------------------------------------------------------+
        ^
        |  2. Dashboard Analytics, Clinical Records, Receipts, Alerts
        v
[ MySQL Database: hospital_management ]
   (patient, doctor, appointment, medical_record, billing, users)
```

#### Inputs & Outputs in Level 0:
1. **Hospital Staff / Administrator to CarePoint**:
   - Authentication credentials (email and password).
   - Patient demographic details (name, gender, date of birth, phone, address).
   - Doctor profiles (name, specialization, department, contact info).
   - Appointment requests (patient ID, doctor ID, date, time slot).
   - Clinical observations (diagnosis text, prescribed medications, examination report).
   - Billing transactions (appointment reference, service fee, payment status, insurance policy).
2. **CarePoint to Hospital Staff / Administrator**:
   - Authentication feedback and session tokens.
   - Real-time aggregate statistics (total patients, doctors, revenue, active appointments).
   - Relational appointment calendars and conflict warnings.
   - Complete electronic health record histories.
   - Formatted, printable billing receipts with hospital header.
   - Referential integrity constraint error explanations.
3. **CarePoint to/from MySQL Database**:
   - Parameterized SQL execution (`INSERT`, `SELECT`, `UPDATE`, `DELETE`).
   - Transaction commitments and rollbacks.
   - Structured relational row sets.

---

### 2. DFD Level 1: Decomposed Process Diagram
The Level 1 diagram decomposes the primary CarePoint system into its five operational modules, illustrating the exact data stores interacted with and the relational data dependencies between them.

- **Diagram File**: [dfd_level1.svg](diagrams/dfd_level1.svg)

#### Process Breakdown:

| Process ID | Process Name | Input Data Flow | Output Data Flow | Data Store |
|---|---|---|---|---|
| **1.0** | **Patient Management** | Registration details, search query, update data, delete request | Patient record cards, medical timeline, validation feedback | `D1: patient` |
| **2.0** | **Doctor Directory** | Doctor profile inputs, specialization, department | Doctor cards, consultation counts, schedule | `D2: doctor` |
| **3.0** | **Appointment Scheduling** | Patient ID, Doctor ID, Date, Time Slot, Status updates | Scheduled appointment feed, conflict alerts | `D3: appointment`<br>*(Validates against D1 & D2)* |
| **4.0** | **Medical Records Charting** | Patient ID, Doctor ID, Appt ID, Diagnosis, Prescriptions | Complete clinical chart, patient diagnosis history | `D4: medical_record`<br>*(Validates against D1, D2 & D3)* |
| **5.0** | **Billing & Revenue Ledger** | Patient ID, Appt ID, Billed Amount, Payment Status | Printable invoice, revenue aggregates | `D5: billing`<br>*(Validates against D1 & D3)* |
| **6.0** | **User Authentication** | Email, password, CSRF token | Session cookie, role permissions | `D6: users` |

#### Data Store Descriptions:
- **`D1: patient`**: Stores permanent patient demographic identifiers, birth dates, and addresses.
- **`D2: doctor`**: Stores hospital medical staff, assigned departments, and specialties.
- **`D3: appointment`**: Stores chronological booking intervals linking patients to physicians.
- **`D4: medical_record`**: Stores confidential clinical evaluations, prescription plans, and laboratory observations.
- **`D5: billing`**: Stores hospital service charges, payment settlement states, and insurance details.
- **`D6: users`**: Stores administrative and staff login accounts with cryptographic password hashes.

#### Inter-Process Relational Validations:
1. **Appointment Validation**: Process `3.0` queries `D1` and `D2` to ensure selected IDs exist. It then checks `D3` to ensure no conflicting booking exists for the same doctor at the designated date and time.
2. **Medical Record Validation**: Process `4.0` verifies from `D3` that the selected appointment belongs strictly to the designated patient and doctor before writing to `D4`.
3. **Billing Validation**: Process `5.0` verifies from `D3` that the selected appointment belongs to the designated patient before recording an invoice into `D5`.

