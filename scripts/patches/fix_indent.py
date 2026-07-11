with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# We can just put the routes OUTSIDE the if statement
new_routes = """
@app.get("/dev-portal/sign-in", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_sign_in():
    return RedirectResponse(url="/sign-in")

@app.get("/dev-portal/login", response_class=HTMLResponse, include_in_schema=False)
async def serve_dev_portal_login():
    return RedirectResponse(url="/login")

"""

text = text.replace(new_routes, "")
text = text.replace("if os.path.exists(react_out_dir):", new_routes + "if os.path.exists(react_out_dir):")

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
