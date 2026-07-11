import sqlite3
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash de contrasena con PBKDF2 + salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        260_000
    ).hex()
    return f"{salt}:{key}"

emails = ["Santi21435@gamil.com", "Santi21435@gmail.com"]
pwd = "Bichosiuu721@"
pwd_hash = hash_password(pwd)

conn = sqlite3.connect('/home/ubuntu/bublee/bublee_ultra.db')
c = conn.cursor()

for email in emails:
    c.execute("SELECT id FROM admins WHERE email = ?", (email,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO admins (chat_id, email, password_hash, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"web_{email}", email, pwd_hash, "Santi", "admin", 1))

conn.commit()
conn.close()
print("Created user successfully!")
