import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    lines = f.readlines()

depth = 0
stack = []
for i in range(14, 412):
    line = lines[i]
    for m in re.finditer(r'<div\b[^>]*>', line):
        stack.append(i+1)
    for m in re.finditer(r'</div\s*>', line):
        if stack:
            stack.pop()

print("Unclosed divs opened at lines:", stack)

