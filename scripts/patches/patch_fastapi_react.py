import re

with open('/home/ubuntu/bublee/src/interfaces/web/app.py', 'r') as f:
    app_code = f.read()

react_route = """
from fastapi.staticfiles import StaticFiles

# Serve the static React export for the Dev Portal
import os
react_out_dir = "/home/ubuntu/bublee-dev-react/out"
if os.path.exists(react_out_dir):
    app.mount("/dev-portal", StaticFiles(directory=react_out_dir, html=True), name="dev-portal")
"""

if 'app.mount("/dev-portal"' not in app_code:
    # insert before @app.get("/app")
    app_code = app_code.replace('@app.get("/app", response_model=None)', react_route + '\n@app.get("/app", response_model=None)')
    with open('/home/ubuntu/bublee/src/interfaces/web/app.py', 'w') as f:
        f.write(app_code)
    with open('/home/ubuntu/.bublee/repo/src/interfaces/web/app.py', 'w') as f:
        f.write(app_code)

print("Patched FastAPI for React!")
