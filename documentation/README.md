# CarePoint Documentation Suite Index

## Hospital Management System (DBMS Mini-Project)

Welcome to the comprehensive technical and academic documentation for the **CarePoint Hospital Management System**. This documentation package has been prepared to meet all university B.Tech/BCA/MCA DBMS course, viva-voce, and lab evaluation criteria.

---

## 1. Documentation Map & Navigation

| Document | Primary Focus | Key Contents | Diagram Asset |
| :--- | :--- | :--- | :---: |
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | Requirements & Architecture | Abstract, Problem Statement, Objectives, Scope, FR-01 to FR-11, Non-Functional Requirements, Tech Stack. | — |
| **[ER_DIAGRAM.md](ER_DIAGRAM.md)** | Database Modeling | Entity-Relationship definitions, Cardinality ratios, Primary/Foreign keys, Attribute domains. | [SVG](diagrams/er_diagram.svg) / [MMD](diagrams/er_diagram.mmd) |
| **[DATA_FLOW_DIAGRAMS.md](DATA_FLOW_DIAGRAMS.md)** | Process Modeling | Context Level-0 DFD and Functional Decomposed Level-1 DFD with data stores (D1–D6) and bidirectional flows. | [DFD-0 SVG](diagrams/dfd_level0.svg) / [DFD-1 SVG](diagrams/dfd_level1.svg) |
| **[SYSTEM_FLOWCHART.md](SYSTEM_FLOWCHART.md)** | Program Logic Flow | End-to-end flowchart: Landing page, Login validation loop, Session creation, Dashboard aggregates, Modules CRUD, Logout. | [Flowchart SVG](diagrams/system_flowchart.svg) |
| **[USE_CASE_DIAGRAM.md](USE_CASE_DIAGRAM.md)** | UML Behavioral Model | Actor definitions (Visitor, Staff, Admin, DBMS), Actor-to-Use-Case Matrix, Detailed specifications (UC-01 to UC-11). | [Use Case SVG](diagrams/use_case_diagram.svg) |
| **[DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)** | Schema & SQL Reference | Full Data Dictionary (6 tables including users.status), 1NF/2NF/3NF/BCNF Normalization Proof, Referential Actions, SQL Query Catalog. | — |
| **[TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)** | QA & Test Evidence | Test Strategy, TC-01 to TC-25 Test Matrix, Pytest execution log (25/25 Passed), Security audit results. | — |
| **[PROJECT_REPORT.md](PROJECT_REPORT.md)** | Academic Project Dossier | Formal 8-chapter project report suitable for project submission, viva binder, and academic presentation. | — |

---

## 2. Visual Diagram Assets (`documentation/diagrams/`)

All diagrams are provided in vector SVG format (resolution-independent for high-quality printing or embedding in PDF submissions):

- **`er_diagram.svg`**: Complete Entity-Relationship Diagram showing 6 tables (`patient`, `doctor`, `appointment`, `medical_record`, `billing`, `users`) with primary keys, foreign keys, and 1:N cardinality connectors.
- **`er_diagram.mmd`**: Editable Mermaid source code for the ER Diagram.
- **`dfd_level0.svg`**: Context Level-0 Data Flow Diagram showing system boundary and external actors.
- **`dfd_level1.svg`**: Level-1 Data Flow Diagram decomposing processes 1.0 to 6.0 across data stores D1 to D6.
- **`system_flowchart.svg`**: Standard ISO system flowchart mapping program execution logic, decision diamonds, and unauthenticated redirect loops.
- **`use_case_diagram.svg`**: UML Use Case diagram with stick figures for Public Visitor, Hospital Staff, and Administrator actors linked to functional use cases.

---

## 3. Quick Start: Running the Verified Application

```bash
# 1. Activate virtual environment or open project directory
cd D:\HMS

# 2. Verify database connection & initialize users table
python -c "import database; database.init_users_table(); print('Database ready!')"

# 3. Create or inspect administrator account
python create_admin.py --name "Dr. Sharma" --email "admin@carepoint.health" --password "Admin@CarePoint2026" --role "Administrator"

# 4. Run automated test suite (25/25 tests pass)
python -m pytest -v tests/test_app.py

# 5. Start the CarePoint Web Application
python app.py
```

Open your browser to:
- **Public Landing Page**: `http://127.0.0.1:5000/`
- **Staff Registration**: `http://127.0.0.1:5000/signup`
- **Staff Login**: `http://127.0.0.1:5000/login`
  - Default Credentials: `admin@carepoint.health` / `Admin@CarePoint2026`
- **Authenticated Dashboard**: `http://127.0.0.1:5000/dashboard`
- **Admin User Governance**: `http://127.0.0.1:5000/admin/users`

