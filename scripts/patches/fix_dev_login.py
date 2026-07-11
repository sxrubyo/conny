with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# We want to change the routes for /dev-portal/sign-in and /dev-portal/login
# Right now they are:
# @app.get("/dev-portal/sign-in", ...)
# async def redirect_old_sign_in(): return RedirectResponse(url="/login")
# @app.get("/dev-portal/login", ...)
# async def redirect_old_login(): return RedirectResponse(url="/login")

new_dev_routes = """
@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/sign-in/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_legacy():
    # Serve the original index.html which contains the Dev Console logic
    legacy_index = Path("/home/ubuntu/bublee/src/interfaces/web/static/index.html")
    if legacy_index.exists():
        return FileResponse(legacy_index)
    return RedirectResponse(url="/sign-in")
"""

text = re.sub(r'@app\.get\("/dev-portal/sign-in".*?async def redirect_old_login\(\):\n    return RedirectResponse\(url="/login"\)', new_dev_routes, text, flags=re.DOTALL)

# ALSO we need to remove @app.get("/login") which I added earlier to serve out/login.html
text = re.sub(r'@app\.get\("/login",.*?return RedirectResponse\(url="/dev-portal/login"\)', '', text, flags=re.DOTALL)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
