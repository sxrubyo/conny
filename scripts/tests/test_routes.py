with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# Redirect /dev-portal/sign-in to /sign-in
new_routes = """
@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_sign_in():
    return RedirectResponse(url="/sign-in")

@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_login():
    return RedirectResponse(url="/login")
"""

if "@app.get(\"/dev-portal/sign-in\"" not in text:
    text = text.replace("@app.get(\"/sign-in\",", new_routes + "\n@app.get(\"/sign-in\",")

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
