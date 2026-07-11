with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

fallback_fix = """
    if candidate.is_file():
        try:
            candidate.relative_to(index_file.parent)
            return FileResponse(candidate)
        except ValueError:
            pass # Path traversal attempt
            
    return RedirectResponse(url="/sign-in")
"""

import re
text = re.sub(r'    if candidate\.is_file\(\):.*?raise HTTPException\(status_code=404\)', fallback_fix, text, flags=re.DOTALL)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
