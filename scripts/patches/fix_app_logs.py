import re
import sqlite3

# Let's create a logs table in bublee_ultra.db and an endpoint.
db_path = "/home/ubuntu/bublee/bublee_ultra.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
# Insert some dummy log so it's not totally empty (but the prompt said "100% reales", so maybe don't insert dummy?)
# Wait, "datos reales" means the system should log real things, or at least pull from a real DB.
conn.commit()
conn.close()

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

api_code = """
@app.get("/api/dev/logs")
async def api_get_logs(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = sqlite3.connect("/home/ubuntu/bublee/bublee_ultra.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 100")
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"logs": logs}
"""

if '@app.get("/api/dev/logs")' not in content:
    insert_idx = content.find('@app.get("/api/dev/users")')
    if insert_idx != -1:
        content = content[:insert_idx] + api_code + "\n" + content[insert_idx:]
        with open(filename, 'w') as f:
            f.write(content)
