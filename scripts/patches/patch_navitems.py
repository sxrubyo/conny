import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Add missing navItems declaration
missing_nav = """
const navItems = document.querySelectorAll('.nav-item');
"""
js = js.replace("// ── Dashboard Navigation ──", missing_nav + "\n// ── Dashboard Navigation ──")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
