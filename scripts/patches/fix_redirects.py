with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# Change redirect of /dev-portal/sign-in to /login instead of /sign-in
text = re.sub(r'async def serve_dev_portal_sign_in\(\):\n    return RedirectResponse\(url="/sign-in"\)', 
              'async def serve_dev_portal_sign_in():\n    return RedirectResponse(url="/login")', text)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
