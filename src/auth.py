"""
auth.py — Authentication & User Management Module
Handles: Registration, Login, Password Hashing, Role-Based Access,
         Failed Login Limiting, Session Timeout, and Activity Logging.
"""

import sqlite3
import bcrypt
import os
import time
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Database path (lives next to app.py)
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
SESSION_TIMEOUT_MINUTES = 15


# ============================= DATABASE SETUP ==============================
def init_database():
    """Create all required tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Viewer',
            date_joined TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TEXT DEFAULT NULL
        )
    """)

    # Activity log table (stores every prediction a user makes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            action_type TEXT NOT NULL,
            input_amount REAL,
            result TEXT,
            confidence REAL,
            threshold_used REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Settings table (stores per-user preferences)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'dark',
            default_threshold REAL DEFAULT 0.5,
            active_model TEXT DEFAULT 'Random Forest',
            auto_clear_data INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================= PASSWORD HASHING ============================
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ============================= REGISTRATION ================================
def register_user(full_name: str, username: str, password: str, role: str = "Viewer") -> dict:
    """
    Register a new user.
    Returns: {"success": True/False, "message": "..."}
    """
    if not full_name.strip() or not username.strip() or not password.strip():
        return {"success": False, "message": "All fields are required."}

    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters."}

    if role not in ("Admin", "Analyst", "Viewer"):
        return {"success": False, "message": "Invalid role selected."}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return {"success": False, "message": "Username already taken."}

        password_hash = hash_password(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO users (full_name, username, password_hash, role, date_joined) VALUES (?, ?, ?, ?, ?)",
            (full_name, username, password_hash, role, now)
        )
        user_id = cursor.lastrowid

        # Create default settings for the new user
        cursor.execute(
            "INSERT INTO settings (user_id) VALUES (?)",
            (user_id,)
        )

        conn.commit()
        return {"success": True, "message": "Account created successfully!"}

    except Exception as e:
        return {"success": False, "message": f"Registration failed: {str(e)}"}
    finally:
        conn.close()


# ============================= LOGIN =======================================
def login_user(username: str, password: str) -> dict:
    """
    Authenticate a user.
    Returns: {"success": True/False, "message": "...", "user": {...} or None}
    """
    if not username.strip() or not password.strip():
        return {"success": False, "message": "Username and password are required.", "user": None}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, full_name, username, password_hash, role, date_joined, failed_attempts, locked_until FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            return {"success": False, "message": "Invalid username or password.", "user": None}

        user_id, full_name, uname, pw_hash, role, date_joined, failed_attempts, locked_until = row

        # --- Check if account is locked ---
        if locked_until:
            lock_time = datetime.strptime(locked_until, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < lock_time:
                remaining = int((lock_time - datetime.now()).total_seconds())
                return {
                    "success": False,
                    "message": f"Account locked. Try again in {remaining} seconds.",
                    "user": None
                }
            else:
                # Lockout expired — reset
                cursor.execute(
                    "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
                    (user_id,)
                )
                conn.commit()
                failed_attempts = 0

        # --- Verify password ---
        if not verify_password(password, pw_hash):
            failed_attempts += 1

            if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                lock_until = (datetime.now() + timedelta(seconds=LOCKOUT_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                    (failed_attempts, lock_until, user_id)
                )
                conn.commit()
                return {
                    "success": False,
                    "message": f"Too many failed attempts. Account locked for {LOCKOUT_SECONDS} seconds.",
                    "user": None
                }
            else:
                cursor.execute(
                    "UPDATE users SET failed_attempts = ? WHERE id = ?",
                    (failed_attempts, user_id)
                )
                conn.commit()
                remaining = MAX_LOGIN_ATTEMPTS - failed_attempts
                return {
                    "success": False,
                    "message": f"Invalid password. {remaining} attempt(s) remaining.",
                    "user": None
                }

        # --- Successful login — reset failed attempts ---
        cursor.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (user_id,)
        )
        conn.commit()

        user_data = {
            "id": user_id,
            "full_name": full_name,
            "username": uname,
            "role": role,
            "date_joined": date_joined
        }

        return {"success": True, "message": "Login successful!", "user": user_data}

    except Exception as e:
        return {"success": False, "message": f"Login error: {str(e)}", "user": None}
    finally:
        conn.close()


# ============================= SESSION HELPERS =============================
def check_session_timeout(last_activity_time: datetime) -> bool:
    """Returns True if the session has expired (exceeded 15 min of inactivity)."""
    if last_activity_time is None:
        return True
    elapsed = datetime.now() - last_activity_time
    return elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


# ============================= ACTIVITY LOGGING ============================
def log_activity(user_id: int, action_type: str, input_amount: float = None,
                 result: str = None, confidence: float = None, threshold: float = None):
    """Log a user action (prediction, login, etc.) to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """INSERT INTO activity_log 
           (user_id, timestamp, action_type, input_amount, result, confidence, threshold_used) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, now, action_type, input_amount, result, confidence, threshold)
    )
    conn.commit()
    conn.close()


def get_user_activity(user_id: int, limit: int = 50) -> list:
    """Retrieve the activity history for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """SELECT timestamp, action_type, input_amount, result, confidence, threshold_used 
           FROM activity_log WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "action": r[1],
            "amount": r[2],
            "result": r[3],
            "confidence": r[4],
            "threshold": r[5]
        }
        for r in rows
    ]


# ============================= SETTINGS ====================================
def get_user_settings(user_id: int) -> dict:
    """Get the saved settings for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT theme, default_threshold, active_model, auto_clear_data FROM settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "theme": row[0],
            "default_threshold": row[1],
            "active_model": row[2],
            "auto_clear_data": bool(row[3])
        }
    return {"theme": "dark", "default_threshold": 0.5, "active_model": "Random Forest", "auto_clear_data": False}


def update_user_settings(user_id: int, **kwargs):
    """Update one or more settings for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    allowed_fields = {"theme", "default_threshold", "active_model", "auto_clear_data"}
    for key, value in kwargs.items():
        if key in allowed_fields:
            if key == "auto_clear_data":
                value = int(value)
            cursor.execute(f"UPDATE settings SET {key} = ? WHERE user_id = ?", (value, user_id))

    conn.commit()
    conn.close()


# ============================= USER MANAGEMENT (Admin) =====================
def get_all_users() -> list:
    """Retrieve all registered users (for Admin panel)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, username, role, date_joined FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": r[0], "full_name": r[1], "username": r[2], "role": r[3], "date_joined": r[4]}
        for r in rows
    ]


def delete_user(user_id: int) -> dict:
    """Delete a user account (Admin only)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM activity_log WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return {"success": True, "message": "User deleted successfully."}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete user: {str(e)}"}
    finally:
        conn.close()


def change_password(user_id: int, old_password: str, new_password: str) -> dict:
    """Change a user's password after verifying the old one."""
    if len(new_password) < 6:
        return {"success": False, "message": "New password must be at least 6 characters."}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "User not found."}

    if not verify_password(old_password, row[0]):
        conn.close()
        return {"success": False, "message": "Current password is incorrect."}

    new_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Password changed successfully!"}


def get_system_stats() -> dict:
    """Get system-wide statistics for the Settings page."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM activity_log")
    total_predictions = cursor.fetchone()[0]

    # Database file size
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    db_size_kb = round(db_size / 1024, 2)

    conn.close()

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "database_size_kb": db_size_kb
    }
