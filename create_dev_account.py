import sqlite3
import os
import sys
import secrets
import hashlib

email = sys.argv[1]
password = sys.argv[2]

db_path = "/home/ubuntu/conny/conny_ultra.db"
if not os.path.exists(db_path):
    db_path = "/home/ubuntu/conny/conny.db"

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        260_000
    ).hex()
    return f"{salt}:{key}"

hashed = hash_password(password)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS dev_accounts (email TEXT PRIMARY KEY, password_hash TEXT)")
c.execute("INSERT OR REPLACE INTO dev_accounts (email, password_hash) VALUES (?, ?)", (email, hashed))
conn.commit()
conn.close()
print(f"Cuenta de dev {email} creada.")
