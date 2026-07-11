import subprocess
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

try:
    from src.core.globals import db
except ImportError:
    db = None

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    chat_id: str = None
    instance: str = "bublee"

@router.post("/chat")
async def dev_chat(request: ChatRequest):
    message = request.message.strip()

    if message.startswith("/"):
        parts = message.split()
        cmd = parts[0][1:]
        args = parts[1:]

        try:
            result = subprocess.run(
                ["python3", "/home/ubuntu/bublee/bublee_cli.py", cmd] + args,
                capture_output=True,
                text=True,
                timeout=15
            )
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = f"Comando /{cmd} ejecutado sin salida."
            return {"reply": output}
        except subprocess.TimeoutExpired:
            return {"reply": f"El comando /{cmd} tardó demasiado en responder."}
        except Exception as e:
            return {"reply": f"Error ejecutando /{cmd}: {e}"}

    # Generate AI response
    try:
        from src.core.globals import llm_engine
        if llm_engine:
            messages = [{"role": "system", "content": "You are Bublee Admin Agent, an AI that manages the dev environment for the user. Be concise, smart, and helpful. Do not mention that you are a language model."}]
            
            # If there's a chat_id context, pass it
            if request.chat_id:
                messages.append({"role": "system", "content": f"The user is currently viewing the chat history for {request.chat_id}."})
                
            messages.append({"role": "user", "content": message})
            
            res, _ = await llm_engine.complete(messages, model_tier="fast")
            if res:
                return {"reply": res}
    except Exception as e:
        print(f"Error in dev_chat: {e}")

    return {"reply": f"[Agent] {message}"}

@router.get("/chats")
async def get_chats():
    if not db:
        return {"conversations": []}

    try:
        chats = db.get_recent_patient_chats(limit=30)
        formatted = []
        for c in chats:
            name = c.get("patient_name") or c.get("chat_id") or "Unknown"
            formatted.append({
                "title": f"Chat with {name}",
                "date": c.get("last_msg_time") or "Recently",
                "chat_id": c.get("chat_id")
            })
        return {"conversations": formatted}
    except:
        return {"conversations": []}
