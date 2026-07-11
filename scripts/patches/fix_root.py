with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "r") as f:
    text = f.read()

import re

# Find serve_spa_root and modify the index_file
text = re.sub(r'index_file = Path\("/home/ubuntu/bublee/src/interfaces/web/static/index\.html"\)',
              'index_file = Path("/home/ubuntu/bublee/src/interfaces/web/static/bublee-landing.html")', text)

with open("/home/ubuntu/bublee/src/interfaces/web/app.py", "w") as f:
    f.write(text)
