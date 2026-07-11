with open('/home/ubuntu/bublee/src/interfaces/web/app.py', 'r') as f:
    code = f.read()

# I want to add:
# @app.get("/dev-portal")
# async def redirect_dev_portal():
#     return RedirectResponse(url="/dev-portal/")
#
# But I must put it BEFORE the catch-all!
import re
new_code = """from fastapi.responses import RedirectResponse
@app.get("/dev-portal")
async def redirect_dev_portal():
    return RedirectResponse(url="/dev-portal/")

@app.get("/{full_path:path}", include_in_schema=False, response_model=None)"""

code = code.replace('@app.get("/{full_path:path}", include_in_schema=False, response_model=None)', new_code)

with open('/home/ubuntu/bublee/src/interfaces/web/app.py', 'w') as f:
    f.write(code)
