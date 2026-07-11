with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# Remove the dev-portal mount
text = text.replace('app.mount("/dev-portal", StaticFiles(directory=react_out_dir, html=True), name="dev-portal")', '')

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
