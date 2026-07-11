import sqlite3
import re

db_path = "/home/ubuntu/bublee/bublee_ultra.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS monthly_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    sales INTEGER NOT NULL,
    target INTEGER NOT NULL
)
""")
c.execute("SELECT COUNT(*) FROM monthly_sales")
if c.fetchone()[0] == 0:
    data = [
        ("Jan", 2150, 3000),
        ("Feb", 3500, 3500),
        ("Mar", 4800, 4200),
        ("Apr", 5100, 4800),
        ("May", 6400, 5000),
        ("Jun", 8200, 7000),
        ("Jul", 9100, 8000)
    ]
    c.executemany("INSERT INTO monthly_sales (month, sales, target) VALUES (?, ?, ?)", data)
conn.commit()
conn.close()

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

new_chart_endpoint = """@app.get("/api/dev/chart")
async def api_get_chart(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    conn = sqlite3.connect("/home/ubuntu/bublee/bublee_ultra.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT month as name, sales, target FROM monthly_sales ORDER BY id ASC")
    chart_data = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return {"chartData": chart_data}"""

content = re.sub(r'@app\.get\("/api/dev/chart"\).*?return \{"chartData": \[.*?\]\}', new_chart_endpoint, content, flags=re.DOTALL)

with open(filename, 'w') as f:
    f.write(content)
