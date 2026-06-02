import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

FALLBACK_MSG = "⚠️ Fallo del modelo LLM. No obtuve respuesta. Por favor, envía tu mensaje nuevamente."

for fpath in files_to_patch:
    with open(fpath, "r") as f:
        content = f.read()

    # Pattern:
    # if not r:
    #     if found:
    #        ...
    #     else:
    #        ...
    # return _send(r)
    
    # Actually, we can just find `if not r:\n            if found:`
    # and replace the whole block until `return _send(r)`
    
    match = re.search(r'if not r:\n\s+if found:.*?\n\s+return _send\(r\)', content, flags=re.DOTALL)
    if match:
        replacement = f'if not r:\n            return _send("{FALLBACK_MSG}")\n        return _send(r)'
        content = content.replace(match.group(0), replacement)
        
    with open(fpath, "w") as f:
        f.write(content)

