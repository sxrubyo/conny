with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

import re

# Find the onboarding blocks
match = re.search(r'(<!-- ONBOARDING: CREAR CUENTA -->.*?</div>\s*</div>)', content, re.DOTALL)
if match:
    onboarding_html = match.group(1)
    
    # Remove it from its current position
    content = content.replace(onboarding_html, '')
    
    # Place it AFTER standard-login-view closes
    # standard-login-view closes just before <!-- Formulario de Acceso Desarrolladores (Devs) -->
    target = '<!-- Formulario de Acceso Desarrolladores (Devs) -->'
    content = content.replace(target, onboarding_html + '\n\n                ' + target)
    
    with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
        f.write(content)
        print("Success")
else:
    print("Match not found")
