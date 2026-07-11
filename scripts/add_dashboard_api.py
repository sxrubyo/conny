import sqlite3

db_path = "/home/ubuntu/bublee/bublee_ultra.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS system_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    location TEXT,
    status TEXT DEFAULT 'Active',
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS country_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    sales_amount INTEGER DEFAULT 0
)
""")
conn.commit()
conn.close()

# Now inject API endpoints into app.py
filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

api_code = """
@app.get("/api/dev/users")
async def api_get_users(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = sqlite3.connect("/home/ubuntu/bublee/bublee_ultra.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM system_users ORDER BY created_at DESC")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"users": users}

@app.post("/api/dev/users")
async def api_add_user(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    data = await request.json()
    conn = sqlite3.connect("/home/ubuntu/bublee/bublee_ultra.db")
    c = conn.cursor()
    c.execute("INSERT INTO system_users (name, email, location, status, balance) VALUES (?, ?, ?, ?, ?)",
              (data.get("name"), data.get("email"), data.get("location", ""), data.get("status", "Active"), data.get("balance", 0.0)))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return {"ok": True, "id": user_id}

@app.get("/api/dev/sales")
async def api_get_sales(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = sqlite3.connect("/home/ubuntu/bublee/bublee_ultra.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM country_sales ORDER BY sales_amount DESC")
    sales = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"sales": sales}
"""

if '@app.get("/api/dev/users")' not in content:
    insert_idx = content.find('@app.get("/api/dev/instances")')
    if insert_idx != -1:
        content = content[:insert_idx] + api_code + "\n" + content[insert_idx:]
        with open(filename, 'w') as f:
            f.write(content)
