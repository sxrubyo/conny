import re
with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Replace the second 'const isDev' with 'let isDev_ignore' just in case, or just comment it out
js = js.replace("const isDev = localStorage.getItem('bublee_dev_mode') === 'true';", "const isDev = localStorage.getItem('bublee_dev_mode') === 'true';", 1)
# Actually, the best way is to rename the first one:
js = js.replace("const isDev = localStorage.getItem('bublee_dev_mode') === 'true';", "const isDevInitial = localStorage.getItem('bublee_dev_mode') === 'true';", 1)
js = js.replace("if (isDev) {\\n            window.location.href = '/dev-portal';", "if (isDevInitial) {\\n            window.location.href = '/dev-portal';")

# Wait, let's just do a simple replacement
