import sqlite3

conn = sqlite3.connect('/home/ubuntu/bublee/instances/ovni/conny.db')
c = conn.cursor()

# Check if clinic table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinic'")
if not c.fetchone():
    c.execute("CREATE TABLE clinic (setup_done INTEGER DEFAULT 0)")

# Check current value
c.execute("SELECT setup_done FROM clinic")
row = c.fetchone()
print("Current setup_done:", row)

# Set it
c.execute("UPDATE clinic SET setup_done = 1")
conn.commit()
print("Updated")

# Verify
c.execute("SELECT setup_done FROM clinic")
print("Now:", c.fetchone())
conn.close()
