with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re
text = text.replace('or normalized in {"api", "openapi.json", "docs", "redoc", "telegram", "whatsapp", "logo", "patients", "conversations", "appointments", "config", "personality", "metrics", "test"}:\n\n    react_out = Path',
'or normalized in {"api", "openapi.json", "docs", "redoc", "telegram", "whatsapp", "logo", "patients", "conversations", "appointments", "config", "personality", "metrics", "test"}:\n        raise HTTPException(status_code=404)\n\n    react_out = Path')

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
