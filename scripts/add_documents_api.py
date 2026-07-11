import re

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

new_api = """
@app.get("/api/dev/documents")
async def api_dev_list_documents(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    import os
    docs = []
    instances_dir = "/home/ubuntu/bublee/instances"
    
    # Base instance docs
    base_docs_dir = "/home/ubuntu/bublee/knowledge"
    if os.path.isdir(base_docs_dir):
        for f in os.listdir(base_docs_dir):
            path = os.path.join(base_docs_dir, f)
            if os.path.isfile(path):
                stat = os.stat(path)
                docs.append({
                    "id": f"bublee-{f}",
                    "instance": "bublee",
                    "filename": f,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })

    if os.path.isdir(instances_dir):
        for entry in os.listdir(instances_dir):
            docs_dir = os.path.join(instances_dir, entry, "knowledge")
            if os.path.isdir(docs_dir):
                for f in os.listdir(docs_dir):
                    path = os.path.join(docs_dir, f)
                    if os.path.isfile(path):
                        stat = os.stat(path)
                        docs.append({
                            "id": f"{entry}-{f}",
                            "instance": entry,
                            "filename": f,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
    return {"documents": docs}

@app.get("/api/notifications")
async def api_list_notifications(request: Request):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    # Mock notifications for now since there's no events table yet
    return {"notifications": [
        {"id": "1", "type": "info", "text": "New conversation started on clinica-de-las-americas", "time": "2 mins ago", "read": False},
        {"id": "2", "type": "warning", "text": "High response time detected on bublee", "time": "1 hour ago", "read": False},
        {"id": "3", "type": "alert", "text": "Instance test-cli-instance went offline", "time": "3 hours ago", "read": True}
    ]}
"""

insert_idx = content.find('@app.get("/api/dev/instances")')
content = content[:insert_idx] + new_api + content[insert_idx:]

with open(filename, 'w') as f:
    f.write(content)
