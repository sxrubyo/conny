import sqlite3
import json

conn = sqlite3.connect('/home/ubuntu/bublee/bublee_ultra.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM clinic WHERE id=1")
row = c.fetchone()
if row:
    print(dict(row))
else:
    print("NO CLINIC ROW!")
