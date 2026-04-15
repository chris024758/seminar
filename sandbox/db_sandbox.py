"""
SQLite dummy database sandbox.

Owns the full lifecycle of a realistic-looking production database:
create, seed, attack (DROP/DELETE), and reset. All operations use
context-manager connections so no file locks are left open on Windows.
"""

import sqlite3
from pathlib import Path

SANDBOX_DIR = Path(__file__).parent
DB_PATH = SANDBOX_DIR / "demo.db"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# ── Seed data ─────────────────────────────────────────────────────────────────

_USERS = [
    (1,  "admin",   "admin@corp.internal",      "superadmin", "2023-01-10"),
    (2,  "alice",   "alice@corp.internal",       "analyst",    "2023-03-15"),
    (3,  "bob",     "bob@corp.internal",         "developer",  "2023-04-02"),
    (4,  "charlie", "charlie@corp.internal",     "developer",  "2023-05-20"),
    (5,  "dave",    "dave@corp.internal",        "manager",    "2023-06-11"),
    (6,  "eve",     "eve@corp.internal",         "analyst",    "2023-07-30"),
    (7,  "frank",   "frank@corp.internal",       "devops",     "2023-09-05"),
    (8,  "grace",   "grace@corp.internal",       "finance",    "2023-11-22"),
]

_ORDERS = [
    (1,  2, "Cloud Storage Plan",      149.99, "completed",  "2024-01-05"),
    (2,  3, "Dev License Pro",         299.00, "completed",  "2024-01-12"),
    (3,  5, "Enterprise Suite",       1200.00, "pending",    "2024-02-01"),
    (4,  6, "Analytics Add-on",        89.99, "completed",  "2024-02-14"),
    (5,  2, "Support Contract",        499.00, "active",     "2024-02-20"),
    (6,  4, "API Access Tier 2",       199.00, "completed",  "2024-03-01"),
    (7,  8, "Compliance Module",       599.00, "pending",    "2024-03-10"),
    (8,  7, "Monitoring Stack",        349.00, "active",     "2024-03-15"),
    (9,  3, "CI/CD Pipeline",          249.00, "completed",  "2024-03-20"),
    (10, 5, "Training Bundle",         799.00, "completed",  "2024-03-25"),
    (11, 6, "Data Warehouse",         1499.00, "pending",    "2024-04-01"),
    (12, 2, "Security Audit",          899.00, "active",     "2024-04-05"),
]

_SESSIONS = [
    (1, 1, "eyJhbGciOiJIUzI1NiJ9.YWRtaW4.xK9mP2nQ", "10.0.1.5",   "2024-04-16 08:00:00"),
    (2, 2, "eyJhbGciOiJIUzI1NiJ9.YWxpY2U.vR4sT7wY", "10.0.1.12",  "2024-04-16 09:30:00"),
    (3, 3, "eyJhbGciOiJIUzI1NiJ9.Ym9i.1zA3bC5d",    "10.0.1.24",  "2024-04-16 10:00:00"),
    (4, 5, "eyJhbGciOiJIUzI1NiJ9.ZGF2ZQ.E6fG8hJ0",  "10.0.1.33",  "2024-04-16 10:15:00"),
    (5, 7, "eyJhbGciOiJIUzI1NiJ9.ZnJhbms.K1lM2nN3", "10.0.1.41",  "2024-04-16 11:00:00"),
    (6, 8, "eyJhbGciOiJIUzI1NiJ9.Z3JhY2U.O4pQ5rS6", "10.0.1.55",  "2024-04-16 11:30:00"),
]

# ── Internal helpers ──────────────────────────────────────────────────────────

def _create_and_seed():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                role TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product TEXT,
                amount REAL,
                status TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                session_token TEXT,
                ip_address TEXT,
                expires_at TEXT
            );
        """)
        c.executemany("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)", _USERS)
        c.executemany("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", _ORDERS)
        c.executemany("INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?)", _SESSIONS)
        conn.commit()

# ── Public API ────────────────────────────────────────────────────────────────

def reset_db():
    """Reset the database with fresh seed data by dropping and recreating tables.

    Does NOT delete the file — avoids Windows file-lock errors when SQLite
    has an open connection from a previous run.
    """
    with sqlite3.connect(DB_PATH, isolation_level=None) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS orders")
        c.execute("DROP TABLE IF EXISTS sessions")
    _create_and_seed()


def get_row_counts() -> dict:
    """Return {table_name: row_count}. Returns 0 for dropped tables."""
    counts = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            for table in ["users", "orders", "sessions"]:
                try:
                    c.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = c.fetchone()[0]
                except sqlite3.OperationalError:
                    counts[table] = 0
    except Exception:
        counts = {"users": 0, "orders": 0, "sessions": 0}
    return counts


def get_table_rows() -> dict:
    """Return {table_name: list[dict]} for dataframe display."""
    tables = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            for table in ["users", "orders", "sessions"]:
                try:
                    c.execute(f"SELECT * FROM {table}")
                    tables[table] = [dict(row) for row in c.fetchall()]
                except sqlite3.OperationalError:
                    tables[table] = []
    except Exception:
        tables = {"users": [], "orders": [], "sessions": []}
    return tables


def execute_delete_attack() -> dict:
    """
    Execute the DELETE DATABASE attack against the sandbox DB.
    Returns before/after snapshots for display.
    """
    counts_before = get_row_counts()
    rows_before   = get_table_rows()

    sql_executed = [
        "DROP TABLE users;",
        "DELETE FROM orders;",
        "DELETE FROM sessions;",
    ]

    try:
        with sqlite3.connect(DB_PATH, isolation_level=None) as conn:
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS users")
            c.execute("DELETE FROM orders")
            c.execute("DELETE FROM sessions")
    except Exception as e:
        sql_executed.append(f"ERROR: {e}")

    counts_after = get_row_counts()

    return {
        "counts_before": counts_before,
        "counts_after":  counts_after,
        "rows_before":   rows_before,
        "sql_executed":  sql_executed,
    }
