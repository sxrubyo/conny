import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    if 'id="login-screen"' in line:
        depth = 1
        print(f"login-screen starts at {i+1}")
        continue
    
    if depth > 0:
        opens = len(re.findall(r'<div\b[^>]*>', line))
        closes = len(re.findall(r'</div\s*>', line))
        depth += (opens - closes)
        if depth == 0:
            print(f"login-screen closes at {i+1}")
            break

