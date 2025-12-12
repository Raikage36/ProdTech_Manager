"""
database_manager.py
-------------------

Central database handler for ProdTech Manager.

Handles:
✅ Database creation & connection
✅ Automatic schema migrations
✅ Safe query execution
✅ All table definitions for:
   - agents
   - attendance
   - vacations
   - disciplinary
   - forms (admin templates)
"""

import sqlite3
from contextlib import closing

# ---------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------
DB_PATH = "prodtech_manager.db"

# ---------------------------------------------------------
# Core Database Functions
# ---------------------------------------------------------
def connect():
    """Create a new connection to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    print(f"🗄 Using DB file: {DB_PATH}")
    return conn

def execute_query(query, params=()):
    """Execute a query with optional parameters (INSERT, UPDATE, DELETE)."""
    try:
        with connect() as conn:
            conn.execute(query, params)
            conn.commit()
    except sqlite3.Error as e:
        print(f"[DB ERROR] {e}")
        raise

def fetch_all(query, params=()):
    """Fetch all rows from a SELECT query."""
    with closing(connect()) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

# ---------------------------------------------------------
# Schema Migration
# ---------------------------------------------------------
def migrate_database():
    """Create or update all required tables and columns."""
    try:
        with connect() as conn:
            cur = conn.cursor()

            # =========================================================
            # 1️⃣ AGENTS TABLE
            # =========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    department TEXT,
                    section TEXT,
                    shift_type TEXT,
                    roster_type TEXT,
                    job_title TEXT,
                    email TEXT,
                    phone TEXT,
                    employer TEXT
                )
            """)

            cur.execute("PRAGMA table_info(agents)")
            existing_cols = [col[1] for col in cur.fetchall()]
            required_agent_cols = {
                "department": "TEXT",
                "section": "TEXT",
                "shift_type": "TEXT",
                "roster_type": "TEXT",
                "job_title": "TEXT",
                "email": "TEXT",
                "phone": "TEXT",
                "employer": "TEXT"
            }

            for col, ctype in required_agent_cols.items():
                if col not in existing_cols:
                    cur.execute(f"ALTER TABLE agents ADD COLUMN {col} {ctype} DEFAULT ''")
                    print(f"✅ Added missing column: agents.{col}")

            # =========================================================
            # 2️⃣ ATTENDANCE TABLE
            # =========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    date TEXT,
                    status TEXT,
                    reason TEXT,
                    FOREIGN KEY(agent_id) REFERENCES agents(id)
                )
            """)

            # =========================================================
            # 3️⃣ VACATIONS TABLE (plural, unified)
            # =========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vacations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    total_days INTEGER,
                    days_used INTEGER DEFAULT 0,
                    status TEXT,
                    reason TEXT,
                    FOREIGN KEY(agent_id) REFERENCES agents(id)
                )
            """)

            # =========================================================
            # 4️⃣ DISCIPLINARY TABLE
            # =========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS disciplinary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    incident_date TEXT,
                    reason TEXT,
                    action_taken TEXT,
                    FOREIGN KEY(agent_id) REFERENCES agents(id)
                )
            """)

            # =========================================================
            # 5️⃣ FORMS TABLE (for administrative form tracking)
            # =========================================================
            cur.execute("""
                CREATE TABLE IF NOT EXISTS forms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_name TEXT,
                    form_type TEXT,
                    created_at TEXT,
                    created_by TEXT,
                    file_path TEXT
                )
            """)

            conn.commit()
            print("✅ Database migration completed successfully.")
            print(fetch_all("SELECT name FROM sqlite_master WHERE type='table';"))

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        raise

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

# --- AGENTS ---
def insert_agent(agent_data):
    """Insert a new agent safely."""
    execute_query("""
        INSERT INTO agents (name, department, section, shift_type, roster_type,
                            job_title, email, phone, employer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_data.get("name", ""),
        agent_data.get("department", ""),
        agent_data.get("section", ""),
        agent_data.get("shift_type", ""),
        agent_data.get("roster_type", ""),
        agent_data.get("job_title", ""),
        agent_data.get("email", ""),
        agent_data.get("phone", ""),
        agent_data.get("employer", "")
    ))

def get_agents():
    """Return all agents ordered by name."""
    return fetch_all("SELECT * FROM agents ORDER BY name ASC")

# --- ATTENDANCE ---
def insert_attendance(agent_id, date, status, reason):
    """Insert attendance record."""
    execute_query("""
        INSERT INTO attendance (agent_id, date, status, reason)
        VALUES (?, ?, ?, ?)
    """, (agent_id, date, status, reason))

def get_attendance(agent_id=None):
    """Get attendance for one or all agents."""
    if agent_id:
        return fetch_all("SELECT * FROM attendance WHERE agent_id = ? ORDER BY date DESC", (agent_id,))
    return fetch_all("SELECT * FROM attendance ORDER BY date DESC")

# --- VACATIONS ---
def insert_vacation(agent_id, start_date, end_date, total_days, status, reason):
    """Insert vacation record."""
    execute_query("""
        INSERT INTO vacations (agent_id, start_date, end_date, total_days, days_used, status, reason)
        VALUES (?, ?, ?, ?, 0, ?, ?)
    """, (agent_id, start_date, end_date, total_days, status, reason))

def get_vacations(agent_id=None):
    """Fetch all or specific agent vacation records."""
    if agent_id:
        return fetch_all("SELECT * FROM vacations WHERE agent_id = ? ORDER BY start_date DESC", (agent_id,))
    return fetch_all("SELECT * FROM vacations ORDER BY start_date DESC")

# --- DISCIPLINARY ---
def insert_disciplinary(agent_id, incident_date, reason, action_taken):
    """Insert disciplinary record."""
    execute_query("""
        INSERT INTO disciplinary (agent_id, incident_date, reason, action_taken)
        VALUES (?, ?, ?, ?)
    """, (agent_id, incident_date, reason, action_taken))

def get_disciplinary(agent_id=None):
    """Fetch disciplinary records."""
    if agent_id:
        return fetch_all("SELECT * FROM disciplinary WHERE agent_id = ? ORDER BY incident_date DESC", (agent_id,))
    return fetch_all("SELECT * FROM disciplinary ORDER BY incident_date DESC")

# --- FORMS ---
def insert_form(form_name, form_type, created_at, created_by, file_path):
    """Insert a record for a generated form."""
    execute_query("""
        INSERT INTO forms (form_name, form_type, created_at, created_by, file_path)
        VALUES (?, ?, ?, ?, ?)
    """, (form_name, form_type, created_at, created_by, file_path))

def get_forms():
    """Return all generated forms."""
    return fetch_all("SELECT * FROM forms ORDER BY created_at DESC")

# ---------------------------------------------------------
# Initialize Database Automatically
# ---------------------------------------------------------
if __name__ == "__main__":
    migrate_database()