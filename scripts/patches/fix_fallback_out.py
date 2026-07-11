with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

new_fallback = """
    index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/bublee-landing.html")
    candidate = (index_file.parent / normalized).resolve()
    
    if candidate.is_file():
        try:
            candidate.relative_to(index_file.parent)
            return FileResponse(candidate)
        except ValueError:
            pass # Path traversal attempt
            
    # Also check Next.js out directory
    react_out = Path("/home/ubuntu/bublee-dev-react/out")
    out_candidate = (react_out / normalized).resolve()
    if out_candidate.is_file():
        try:
            out_candidate.relative_to(react_out)
            return FileResponse(out_candidate)
        except ValueError:
            pass

    return RedirectResponse(url="/sign-in")
"""

import re
text = re.sub(r'    index_file = Path.*return RedirectResponse\(url="/sign-in"\)', new_fallback, text, flags=re.DOTALL)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
