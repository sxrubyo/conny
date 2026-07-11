with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/index.html")' in line:
        new_lines.append('    index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/bublee-landing.html")\n')
    elif 'return HTMLResponse("<h1>Bublee Dashboard Not Found</h1>' in line:
        pass # remove the 404 response
    elif 'raise HTTPException(status_code=404)' in line and 'normalized.startswith' not in line:
        # This is at the end of spa_fallback
        new_lines.append("""
    react_out = Path("/home/ubuntu/bublee-dev-react/out")
    out_candidate = (react_out / normalized).resolve()
    if out_candidate.is_file():
        try:
            out_candidate.relative_to(react_out)
            return FileResponse(out_candidate)
        except ValueError:
            pass

    return RedirectResponse(url="/sign-in")
""")
    else:
        new_lines.append(line)

# Now inject the explicit routes and the next mount right before serve_spa_dashboard
code = "".join(new_lines)
injection = """
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
import os

react_out_dir = "/home/ubuntu/bublee-dev-react/out"
if os.path.exists(react_out_dir + "/_next"):
    app.mount("/_next", StaticFiles(directory=react_out_dir + "/_next"), name="next-static")

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

@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/sign-in/", response_class=HTMLResponse, include_in_schema=False)
async def redirect_old_sign_in():
    return RedirectResponse(url="/login")

@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login/", response_class=HTMLResponse, include_in_schema=False)
async def redirect_old_login():
    return RedirectResponse(url="/login")

"""
code = code.replace('@app.get("/app", response_model=None)', injection + '\n@app.get("/app", response_model=None)')

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(code)
