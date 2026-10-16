# auth.py  -  Login step 1: the guest book (database) and password helpers
import os
import re
import sqlite3
import tempfile

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- The guest book ----------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # lets us read columns by name
    return conn


def init_db():
    """Create the users table if it does not exist yet."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ---------- Checking the sign-up form ----------
def validate_registration(name, email, password, confirm):
    """Returns a dict of problems. An empty dict means everything is fine."""
    errors = {}

    name = (name or "").strip()
    if not 2 <= len(name) <= 50:
        errors["name"] = "Name must be 2 to 50 characters."

    email = (email or "").strip()
    if not EMAIL_PATTERN.match(email) or len(email) > 120:
        errors["email"] = "Please enter a valid email address."

    password = password or ""
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    elif not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        errors["password"] = "Password must contain at least one letter and one number."
    elif len(password) > 100:
        errors["password"] = "Password is too long (max 100 characters)."

    if password != (confirm or ""):
        errors["confirm"] = "The two passwords do not match."

    return errors


# ---------- Adding and finding users ----------
def create_user(name, email, password):
    """Save a new user. Returns (True, None) or (False, "reason")."""
    email = email.strip().lower()
    password_hash = generate_password_hash(password)   # scramble the password
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email, password_hash),
            )
        return True, None
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


def check_login(email, password):
    """Returns the user row if the email and password are right, else None."""
    email = (email or "").strip().lower()
    with get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is not None and check_password_hash(user["password_hash"], password or ""):
        return user
    return None


def get_user_by_id(user_id):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------- Self-check: run  python auth.py  (uses a throw-away database) ----------
if __name__ == "__main__":
    DB_PATH = os.path.join(tempfile.mkdtemp(), "demo.db")
    init_db()

    print("1. Weak sign-up form  :", validate_registration("A", "bad-email", "abc", "xyz"))
    print("2. Good sign-up form  :", validate_registration("Asha", "asha@example.com", "Study2024", "Study2024"))
    print("3. Create user        :", create_user("Asha", "Asha@Example.com", "Study2024"))
    print("4. Same email again   :", create_user("Other", "asha@example.com", "Another99"))
    print("5. Login, right pass  :", bool(check_login("asha@example.com", "Study2024")))
    print("6. Login, wrong pass  :", bool(check_login("asha@example.com", "wrongpass1")))
    print("7. Login, unknown user:", bool(check_login("nobody@example.com", "Study2024")))

    saved = get_user_by_id(1)["password_hash"]
    print("8. What is stored     :", saved[:40] + "...")
    print("   Is it the real password?", "Study2024" in saved)