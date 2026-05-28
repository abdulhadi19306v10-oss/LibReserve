# LibReserve: Library Book Reservation System

**LibReserve** is a comprehensive, documentation-centric, web-based Library Book Reservation System designed specifically for university library ecosystems. It enables authorized students and faculty members to search the catalog, view real-time availability, and reserve books in advance.

This project was built from scratch using a modern **Python FastAPI backend** and a premium, responsive **glassmorphic dark-theme HTML5/CSS3/JavaScript frontend**.

---

## 👥 Authors & Team Roles

*   **Abdul Hadi** (2025(s)-SE-5): System Architecture, Database Design, Frontend & Backend Development.
*   **Muhammad Irfan** (2025(s)-SE-4): Interface Design, Wireframing, UX, and Manual Verification.
*   **Arslan Liaqat** (2025(s)-SE-30): Requirements Specification, UML Modeling, and Documentation.

---

## 🛠️ Technology Stack

*   **Backend Application:** Python 3.13+ with **FastAPI** (Fast, modern Web API framework)
*   **Data Tier (Database):** **SQLite** (Lightweight, single-file relational database)
*   **Object-Relational Mapping (ORM):** **SQLAlchemy**
*   **Request/Response Validation:** **Pydantic**
*   **Frontend Presentation:** Modern **HTML5**, **CSS3 (Vanilla Glassmorphic stylesheet)**, and **JavaScript (ES6)**
*   **Development Methodology:** Waterfall Lifecycle Model with adjacent feedback loops

---

## 🚀 Key Features by User Role

### 1. Student Portal
*   Browse the university library catalog with real-time availability.
*   Search by Book Title, Author, or ISBN; filter search results by categories.
*   Place advance reservations (holds) specifying expected pickup dates.
*   Cancel pending holds if schedules change.
*   View active book loans, due dates, outstanding overdue fines, and course-curriculum recommendations.

### 2. Faculty / Teacher Portal
*   Perform all standard catalog search and advance holds.
*   Request extended loan periods for deep research materials.
*   Designate academic course reserves for classes (e.g. assigning syllabus books to specific courses).
*   Submit procurement proposals for new library books.

### 3. Librarian Desk
*   Review all pending reservation requests (Approve or Reject with reasons).
*   Check-out workflow: Handover approved books to patrons and mark loans as "Issued".
*   Check-in workflow: Process returned books and automatically calculate overdue fines (Rs. 50 per day).
*   Manage library catalog (Add new acquisitions or delete old records).
*   View real-time logs of daily transactions (T7 metrics).

### 4. Library Admin Portal
*   Monitor dashboard KPIs (Total Branches, Registered Accounts, Catalog Size, Fine Revenue).
*   Toggle patron account states (Block/Suspend students violating policies, or Restore accounts).
*   Review historical circulation metrics (5-month statistics chart).

### 5. System Admin Root Console
*   Monitor server availability uptime and database query load.
*   Run backup checkpoints (SQLite database file state copy).
*   Perform database restores from backups in case of failure.
*   Examine administrative logs of all system operations.

---

## 📦 Directory Structure

```
implementation/
├── backend/
│   ├── auth.py          # Hashing and encryption utilities
│   ├── database.py      # SQLAlchemy connection setup
│   ├── main.py          # FastAPI servers & routing controllers
│   ├── models.py        # Database entities schema definitions
│   └── seed.py          # Seeder script containing mock records
├── frontend/
│   ├── css/
│   │   └── style.css    # Premium glassmorphism dark theme
│   ├── js/
│   │   ├── app.js       # Main state manager & API fetch client
│   │   └── dashboards.js# Dashboards UI loaders & action handlers
│   ├── dashboards/
│   │   ├── student.html, faculty.html, librarian.html,
│   │   ├── lib_admin.html, sys_admin.html
│   ├── login.html       # Single Page Login & Registration
│   └── index.html       # Landing router
├── tests/
│   └── test_api.py      # Integration testing script
├── requirements.txt     # Python dependencies list
├── run.py               # Auto-seeder and application launcher
└── README.md            # System documentation manual
```

---

## 🚦 Installation & Getting Started

### Prerequisites
*   Python 3.12 or 3.13 installed.
*   FastAPI, Uvicorn, and SQLAlchemy packages.

### Run Automatically (Recommended)
Double-click [run.py](file:///c:/Users/Abdul%20Hadi/Desktop/SE/implementation/run.py) or execute it from the project root:
```bash
python run.py
```
This script will:
1.  Check for the database file (`libreserve.db`). If it does not exist, it automatically initializes and populates it with realistic records.
2.  Launch the Uvicorn web server at `http://127.0.0.1:8000`.
3.  Open the system's default web browser to the Login interface.

---

## 🔑 Viva Test Credentials

Use these preloaded users to demonstrate role workflows:

| Role | Username (Email) | Password | Key Actions |
| :--- | :--- | :--- | :--- |
| **Student** | `abdulhadi@uet.edu.pk` | `student123` | Reserve a book, view active holds/loans. |
| **Student (Blocked)** | `suspended_student@uet.edu.pk` | `student123` | Demonstrate login block feature. |
| **Faculty** | `zeeshan@uet.edu.pk` | `faculty123` | Request purchase, add course reserves. |
| **Librarian** | `librarian@uet.edu.pk` | `lib123` | Approve holds, issue/return books. |
| **Library Admin** | `libadmin@uet.edu.pk` | `admin123` | Suspend/Activate students, view revenue. |
| **System Admin** | `sysadmin@uet.edu.pk` | `sys123` | Review audit logs, trigger database backups. |

---

## 🧪 Verification & Automated Testing

To run the automated suite which checks user logs, reservation checks, catalog queries, approvals, and check-ins:
```bash
python tests/test_api.py
```
This starts a mock server instances, makes direct HTTP requests, and verifies success codes.
