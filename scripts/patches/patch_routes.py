import re

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    content = f.read()

new_root_route = """
@app.get("/", response_model=None)
async def serve_landing_page():
    landing_file = Path("/home/ubuntu/bublee-landing/index.html")
    if landing_file.is_file():
        return FileResponse(landing_file)
    return HTMLResponse("<h1>Landing Page Not Found</h1>", status_code=404)
"""

# Insert new root route just above the dashboard route
content = content.replace('@app.get("/dashboard", response_model=None)', new_root_route + '\n@app.get("/dashboard", response_model=None)')

# Update the fallback routing to exclude /dashboard and still serve dashboard SPA for unresolved paths?
# Or just let /dashboard be the dashboard, and / serve landing.
# But wait, SPA routing usually needs to fallback to dashboard.
# I will make the fallback explicitly serve the Dashboard.

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(content)
