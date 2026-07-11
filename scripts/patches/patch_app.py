with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

# Replace serve_spa_root
new_serve_root = """@app.get("/", response_model=None)
async def serve_spa_root():
    index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/bublee-landing.html")
    if index_file.is_file():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Bublee Dashboard Not Found</h1><p>Ensure static assets exist in src/interfaces/web/static</p>", status_code=404)"""

import re
text = re.sub(r'@app\.get\("/", response_model=None\)\nasync def serve_spa_root\(\):.*?return HTMLResponse\("<h1>Bublee Dashboard Not Found</h1><p>Ensure static assets exist in src/interfaces/web/static</p>", status_code=404\)', new_serve_root, text, flags=re.DOTALL)

# Inject explicitly before serve_spa_root
injection = """
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
import os

react_out_dir = "/home/ubuntu/bublee-dev-react/out"
if os.path.exists(react_out_dir + "/_next"):
    app.mount("/_next", StaticFiles(directory=react_out_dir + "/_next"), name="next-static")

@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/sign-in/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_legacy():
    legacy_index = Path("/home/ubuntu/bublee/src/interfaces/web/static/index.html")
    if legacy_index.exists():
        return FileResponse(legacy_index)
    return RedirectResponse(url="/sign-in")

@app.get("/sign-in", response_class=HTMLResponse, include_in_schema=False)
@app.get("/sign-in/", response_class=HTMLResponse, include_in_schema=False)
async def serve_sign_in():
    p = Path("/home/ubuntu/bublee-dev-react/out/sign-in.html")
    if p.exists():
        return p.read_text()
    return RedirectResponse(url="/")
"""
text = text.replace('@app.get("/", response_model=None)', injection + '\n@app.get("/", response_model=None)')

# Replace spa_fallback
old_fallback = """@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str):
    normalized = full_path.lstrip("/")
    if normalized.startswith("api/") or normalized.startswith("webhook/") or normalized.startswith("obs/") or normalized in {"api", "openapi.json", "docs", "redoc", "telegram", "whatsapp", "logo", "patients", "conversations", "appointments", "config", "personality", "metrics", "test"}:
        raise HTTPException(status_code=404)
        
    index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/index.html")
    candidate = (index_file.parent / normalized).resolve()
    
    if candidate.is_file():
        try:
            candidate.relative_to(index_file.parent)
            return FileResponse(candidate)
        except ValueError:
            pass # Path traversal attempt
            
    if index_file.is_file():
        return FileResponse(index_file)
        
    raise HTTPException(status_code=404)"""

new_fallback = """@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str):
    normalized = full_path.lstrip("/")
    if normalized.startswith("api/") or normalized.startswith("webhook/") or normalized.startswith("obs/") or normalized in {"api", "openapi.json", "docs", "redoc", "telegram", "whatsapp", "logo", "patients", "conversations", "appointments", "config", "personality", "metrics", "test"}:
        raise HTTPException(status_code=404)
        
    index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/index.html")
    candidate = (index_file.parent / normalized).resolve()
    
    if candidate.is_file():
        try:
            candidate.relative_to(index_file.parent)
            return FileResponse(candidate)
        except ValueError:
            pass # Path traversal attempt
            
    # Check Next.js out directory
    react_out = Path("/home/ubuntu/bublee-dev-react/out")
    out_candidate = (react_out / normalized).resolve()
    if out_candidate.is_file():
        try:
            out_candidate.relative_to(react_out)
            return FileResponse(out_candidate)
        except ValueError:
            pass
            
    out_html = react_out / f"{normalized}.html"
    if out_html.is_file():
        try:
            out_html.relative_to(react_out)
            return FileResponse(out_html)
        except ValueError:
            pass

    return RedirectResponse(url="/sign-in")"""

text = text.replace(old_fallback, new_fallback)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
