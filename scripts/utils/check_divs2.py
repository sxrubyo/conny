import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    lines = f.readlines()

depth = 0
for i in range(14, 415):
    line = lines[i]
    if 'id="login-screen"' in line:
        depth = 1
        continue
    if depth > 0:
        opens = len(re.findall(r'<div\b[^>]*>', line))
        closes = len(re.findall(r'</div\s*>', line))
        depth += (opens - closes)
        if 'id="onboarding-screen"' in line:
            print(f"Depth at onboarding-screen: {depth}")
            break

