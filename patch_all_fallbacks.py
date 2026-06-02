import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

FALLBACK_MSG = "⚠️ Fallo del modelo LLM. No obtuve respuesta. Por favor, envía tu mensaje nuevamente."

for fpath in files_to_patch:
    with open(fpath, "r") as f:
        content = f.read()
    
    # Pattern 1: return _send(r or fallback)
    content = re.sub(r'return _send\(r or fallback\)', f'return _send(r if r else "{FALLBACK_MSG}")', content)
    
    # Pattern 2: return _send(r or "...")
    content = re.sub(r'return _send\(r or "(.*?)"\)', f'return _send(r if r else "{FALLBACK_MSG}")', content)
    
    # Pattern 3: return _send((r or f"...") + _next_trick())
    content = re.sub(r'return _send\(\(r or f"(.*?)"\) \+ _next_trick\(\)\)', f'return _send((r + _next_trick()) if r else "{FALLBACK_MSG}")', content)
    
    # Pattern 4: if not r: r = _demo_customer_last_resort(text)
    # in demo_handler:3508
    content = re.sub(
        r'if not r:\n\s*r = _demo_customer_last_resort\(text\)',
        f'if not r:\n        r = "{FALLBACK_MSG}"',
        content
    )
    
    # Pattern 5:
    # if not r:
    #    if found: r = _lang_text(...)
    #    else: ...
    # This is a bit more complex, it's inside `_demo_owner_learn_mode_response`.
    # Let's see if we can patch `_demo_owner_learn_mode_response` manually.
    
    with open(fpath, "w") as f:
        f.write(content)

