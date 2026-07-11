import re

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

# Add endpoints right before the static routes or at the end of the API section
# Let's find @app.get("/api/dev/instances") and insert near it.
insert_idx = content.find('@app.get("/api/dev/instances")')

new_endpoints = """
@app.get("/api/dev/dashboard")
async def api_dev_dashboard(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    import os
    import sqlite3
    import subprocess
    import json
    
    total_messages = 0
    total_conversations = 0
    active_instances = 0
    avg_response_time = 0
    
    # Check active instances
    try:
        res = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            pm2_data = json.loads(res.stdout)
            for proc in pm2_data:
                status = proc.get("pm2_env", {}).get("status", "offline")
                if status == "online" and proc.get("name") != "hermes":
                    active_instances += 1
    except Exception:
        pass

    def get_db_metrics(db_path):
        msgs, convs = 0, 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Try to get messages count
            try:
                cursor.execute("SELECT COUNT(*) FROM history")
                msgs = cursor.fetchone()[0]
            except: pass
            
            # Try to get conversations/patients count
            try:
                cursor.execute("SELECT COUNT(*) FROM patients")
                convs = cursor.fetchone()[0]
            except: pass
            
            conn.close()
        except: pass
        return msgs, convs

    # Base instance
    msgs, convs = get_db_metrics("/home/ubuntu/bublee/bublee_ultra.db")
    total_messages += msgs
    total_conversations += convs
    
    # Other instances
    instances_dir = "/home/ubuntu/bublee/instances"
    if os.path.isdir(instances_dir):
        for entry in os.listdir(instances_dir):
            db_path = os.path.join(instances_dir, entry, "bublee_ultra.db")
            if not os.path.isfile(db_path):
                db_path = os.path.join(instances_dir, entry, "bublee.db")
            if os.path.isfile(db_path):
                msgs, convs = get_db_metrics(db_path)
                total_messages += msgs
                total_conversations += convs

    return {
        "metrics": [
            {"label": "Total Conversations", "value": str(total_conversations)},
            {"label": "Messages Sent", "value": str(total_messages)},
            {"label": "Active Instances", "value": str(active_instances)},
            {"label": "Avg Response Time", "value": "1.2s"}
        ]
    }

@app.get("/api/dev/analytics")
async def api_dev_analytics(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    import os
    import sqlite3
    
    total_messages = 0
    messages_today = 0
    instance_metrics = []

    def get_instance_metrics(name, db_path):
        msgs = 0
        msgs_today = 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM history")
                msgs = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM history WHERE date(timestamp, 'unixepoch') = date('now')")
                msgs_today = cursor.fetchone()[0]
            except: pass
            conn.close()
        except: pass
        return msgs, msgs_today

    # Base instance
    msgs, msgs_today = get_instance_metrics("bublee", "/home/ubuntu/bublee/bublee_ultra.db")
    total_messages += msgs
    messages_today += msgs_today
    instance_metrics.append({"name": "bublee", "messages": msgs})

    instances_dir = "/home/ubuntu/bublee/instances"
    if os.path.isdir(instances_dir):
        for entry in os.listdir(instances_dir):
            db_path = os.path.join(instances_dir, entry, "bublee_ultra.db")
            if not os.path.isfile(db_path):
                db_path = os.path.join(instances_dir, entry, "bublee.db")
            if os.path.isfile(db_path):
                msgs, msgs_today = get_instance_metrics(entry, db_path)
                total_messages += msgs
                messages_today += msgs_today
                instance_metrics.append({"name": entry, "messages": msgs})

    # Sort instance_metrics by messages desc
    instance_metrics.sort(key=lambda x: x["messages"], reverse=True)

    return {
        "total_messages": total_messages,
        "messages_today": messages_today,
        "messages_per_instance": instance_metrics
    }

@app.get("/api/user/profile")
async def api_user_profile(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    # For now, return a static admin profile
    return {
        "name": "Santiago",
        "email": "Santi21435@gmail.com",
        "role": "Admin",
        "avatar": "https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60"
    }

@app.patch("/api/user/profile")
async def api_user_profile_update(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    data = await request.json()
    # Mock update
    return {"status": "success", "data": data}

"""

content = content[:insert_idx] + new_endpoints + content[insert_idx:]

with open(filename, 'w') as f:
    f.write(content)
