with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re
text = text.replace('    if index_file.is_file():\n        return FileResponse(index_file)', '')

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
