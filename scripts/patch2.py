import re
with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

new_routes = """
@app.get("/app", response_model=None)
async def serve_spa_dashboard():
    return RedirectResponse(url="/sign-in")

@app.get("/sign-in", response_class=HTMLResponse, include_in_schema=False)
async def serve_sign_in():
    p = Path("/home/ubuntu/bublee-dev-react/out/sign-in.html")
    if p.exists():
        return p.read_text()
    return RedirectResponse(url="/dev-portal/sign-in")

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def serve_login():
    p = Path("/home/ubuntu/bublee-dev-react/out/login.html")
    if p.exists():
        return p.read_text()
    return RedirectResponse(url="/dev-portal/login")
"""

text = re.sub(r'@app\.get\("/app", response_model=None\).*?return HTMLResponse\("<h1>Bublee Dashboard Not Found</h1>", status_code=404\)', new_routes, text, flags=re.DOTALL)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
