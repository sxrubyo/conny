import re

with open('/home/ubuntu/bublee/src/interfaces/web/app.py', 'r') as f:
    content = f.read()

# Let's add a middleware for /dev-portal
# We can use @app.middleware("http")
middleware_code = '''
from fastapi import Request
from fastapi.responses import RedirectResponse

@app.middleware("http")
async def check_dev_portal_auth(request: Request, call_next):
    if request.url.path.startswith("/dev-portal"):
        # Exempt login related stuff and assets if needed, but since it's a SPA, everything is under /dev-portal/
        # Check if auth token exists
        # Actually, let's just check if there is an admin_id in the session
        # or we check the /api/dev/check-auth endpoint logic
        if not request.cookies.get("admin_session"):
            # Check if it's the login page itself or an asset
            if not getattr(request.state, "skip_auth", False): # just a safe fallback
                return RedirectResponse(url="/api/auth/login")
    response = await call_next(request)
    return response

'''

# Wait, `admin_session` cookie is what we use? Let's check api/dev/check-auth.
