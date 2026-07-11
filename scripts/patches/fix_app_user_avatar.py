import re

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

# Add avatar column if it doesn't exist. Wait, I'll just ALTER TABLE if it's there.
# Since this DB is new (created in the previous step), I can just add it.

import sqlite3
db_path = "/home/ubuntu/bublee/bublee_ultra.db"
conn = sqlite3.connect(db_path)
try:
    conn.execute("ALTER TABLE system_users ADD COLUMN avatar TEXT")
except sqlite3.OperationalError:
    pass # column might already exist

# Update API
content = content.replace('c.execute("INSERT INTO system_users (name, email, location, status, balance) VALUES (?, ?, ?, ?, ?)",', 'c.execute("INSERT INTO system_users (name, email, location, status, balance, avatar) VALUES (?, ?, ?, ?, ?, ?)",')
content = content.replace('data.get("status", "Active"), data.get("balance", 0.0)))', 'data.get("status", "Active"), data.get("balance", 0.0), data.get("avatar", "")))')

with open(filename, 'w') as f:
    f.write(content)
