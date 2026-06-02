import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

def apply_rule(content):
    # Reemplazamos `return _send(r or fallback)`
    # Reemplazamos `return _send((r or f"..."))`
    
    # Rule 1: `return _send(r or fallback)`
    # We can replace it with:
    # if r: return _send(r)
    # else:
    #     self._demo_sessions[b"pending_fallback"] = fallback
    #     return _send("⚠️ Fallo de modelo LLM. ¿Deseas ver la respuesta de contingencia (fallback)? Responde 'sí'.")
    
    # We will do this via regex
    return content

# We'll just write a custom script that replaces occurrences of `return _send(r or `
# Actually, wait, it's easier to patch the specific lines manually.
