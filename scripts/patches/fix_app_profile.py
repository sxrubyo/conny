import re

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

profile_code = """
import json
import os

PROFILE_FILE = "/home/ubuntu/bublee/user_profile.json"

def get_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {
        "name": "Santiago",
        "email": "Santi21435@gmail.com",
        "role": "Admin",
        "avatar": "https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60"
    }

def save_profile(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f)

@app.get("/api/user/profile")
async def api_user_profile(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    return get_profile()

@app.patch("/api/user/profile")
async def api_user_profile_update(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    data = await request.json()
    profile = get_profile()
    for k, v in data.items():
        profile[k] = v
    save_profile(profile)
    return {"status": "success", "data": profile}
"""

# Replace the existing profile endpoints
# Find where api_user_profile is defined
start_idx = content.find('@app.get("/api/user/profile")')
end_idx = content.find('@app.get("/api/dev/instances")')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + profile_code + "\n" + content[end_idx:]
    with open(filename, 'w') as f:
        f.write(content)
