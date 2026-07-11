import sqlite3

conn = sqlite3.connect('/home/ubuntu/bublee/bublee_ultra.db')
c = conn.cursor()

# update all admin emails to lowercase
c.execute("UPDATE admins SET email = lower(email)")
conn.commit()
conn.close()
print("Fixed emails to lowercase")
