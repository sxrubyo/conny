with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# Remove the ones after
text = re.sub(r'@app\.get\("/dev-portal/sign-in".*?RedirectResponse\(url="/login"\)\n', "", text, flags=re.DOTALL)

# Insert them before app.mount
new_routes = """
@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_sign_in():
    return RedirectResponse(url="/sign-in")

@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_login():
    return RedirectResponse(url="/login")

"""

text = text.replace("    app.mount(\"/dev-portal\",", new_routes + "    app.mount(\"/dev-portal\",")

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
