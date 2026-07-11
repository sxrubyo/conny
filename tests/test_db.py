import sys
sys.path.append("/home/ubuntu/bublee")
from src.core.globals import db

with db._conn() as c:
    row = c.execute("SELECT name, email, role FROM admins WHERE role = 'owner' LIMIT 1").fetchone()
    print(dict(row))
