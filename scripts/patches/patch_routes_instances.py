import re

with open('/home/ubuntu/bublee/src/bublee/api/routes.py', 'r') as f:
    content = f.read()

instances_endpoints = """
from pydantic import BaseModel
import uuid
import os
import shutil

class InstanceCreateRequest(BaseModel):
    name: str
    admin_email: str
    model: str = "google/gemini-2.5-flash"
    system_prompt: str = ""

@app.get("/api/dev/instances")
async def list_instances(request: Request):
    # Here we should fetch from db or read directories in instances/
    # For now, let's list the clinics from the db plus a mock one if needed
    try:
        clinic = db.get_clinic()
        instances = []
        if clinic:
            instances.append({
                "id": clinic.get("id", "main"),
                "name": clinic.get("name", "Clínica Principal"),
                "admin_email": clinic.get("email", ""),
                "status": "Active",
                "model": "gemini-2.5-flash",
                "created_at": "2024-01-01"
            })
        
        # Read from instances folder
        base_dir = "/home/ubuntu/bublee/instances"
        if os.path.exists(base_dir):
            for d in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, d)):
                    instances.append({
                        "id": d,
                        "name": f"Instance {d}",
                        "admin_email": "admin@example.com",
                        "status": "Active",
                        "model": "gemini-2.5-flash",
                        "created_at": "2024-01-01"
                    })
                    
        return {"ok": True, "instances": instances}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/dev/instances")
async def create_instance(req: InstanceCreateRequest):
    try:
        new_id = str(uuid.uuid4())[:8]
        instance_dir = f"/home/ubuntu/bublee/instances/{new_id}"
        os.makedirs(instance_dir, exist_ok=True)
        # Mock creation
        with open(f"{instance_dir}/config.json", "w") as f:
            f.write(f'{{"name": "{req.name}", "model": "{req.model}"}}')
            
        return {"ok": True, "instance_id": new_id, "message": "Instancia creada con éxito"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/api/dev/instances/{instance_id}")
async def delete_instance(instance_id: str):
    try:
        if instance_id == "main":
            return {"ok": False, "error": "No se puede eliminar la instancia principal"}
            
        instance_dir = f"/home/ubuntu/bublee/instances/{instance_id}"
        if os.path.exists(instance_dir):
            shutil.rmtree(instance_dir)
            return {"ok": True, "message": "Instancia eliminada"}
        else:
            return {"ok": False, "error": "Instancia no encontrada"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
"""

if "@app.get(\"/api/dev/instances\")" not in content:
    # Append at the end
    with open('/home/ubuntu/bublee/src/bublee/api/routes.py', 'a') as f:
        f.write("\n" + instances_endpoints)
