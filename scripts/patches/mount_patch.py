with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

mounts = """
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
react_out_dir = "/home/ubuntu/bublee-dev-react/out"
if os.path.exists(react_out_dir):
    app.mount("/dev-portal", StaticFiles(directory=react_out_dir, html=True), name="dev-portal")
    app.mount("/_next", StaticFiles(directory=react_out_dir + "/_next"), name="next-static")

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

@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
"""

text = text.replace("@app.get(\"/{full_path:path}\", include_in_schema=False, response_model=None)", mounts)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
