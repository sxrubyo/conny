with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

new_routes = """
@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/sign-in/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_sign_in():
    return RedirectResponse(url="/sign-in")

@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
@app.get("/dev-portal/login/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_login():
    return RedirectResponse(url="/login")
"""

text = re.sub(r'@app\.get\("/dev-portal/sign-in".*?RedirectResponse\(url="/login"\)', new_routes, text, flags=re.DOTALL)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
