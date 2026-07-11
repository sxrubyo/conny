import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Delete duplicate dev login block
dead_code_regex = r"// ── Developer Login Handlers ──.*?// Elementos de Acceso Estándar Multi-paso"
js = re.sub(dead_code_regex, "// Elementos de Acceso Estándar Multi-paso", js, flags=re.DOTALL)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
