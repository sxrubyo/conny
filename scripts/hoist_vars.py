import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Find all 'const varName = document.getElementById(...);'
# and 'const varName = document.querySelector(...);'
declarations = re.findall(r'^(const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(document\.(?:getElementById|querySelector(?:All)?)\([^\)]+\));', js, flags=re.MULTILINE)

# Remove them from their original places
for decl_type, var_name, expr in declarations:
    pattern = r'^' + decl_type + r'\s+' + var_name + r'\s*=\s*' + re.escape(expr) + r';'
    js = re.sub(pattern, '', js, flags=re.MULTILINE)

# Construct the hoisted block
hoisted = "// Hoisted DOM Elements\n"
for decl_type, var_name, expr in declarations:
    hoisted += f"var {var_name} = {expr};\n"

# Insert after "// DOM Elements"
js = js.replace('// DOM Elements\n', '// DOM Elements\n' + hoisted)

# Also fix the duplicate devLoginFormNew handler
dead_code_regex = r"// ── Developer Login Handlers ──.*?// Elementos de Acceso Estándar Multi-paso"
js = re.sub(dead_code_regex, "// Elementos de Acceso Estándar Multi-paso", js, flags=re.DOTALL)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
