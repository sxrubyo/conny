with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

import re

# Find the waitlist block
match = re.search(r'(<!-- ONBOARDING: BETA WAITLIST -->.*?</div>\s*</div>)', content, re.DOTALL)
if match:
    waitlist_html = match.group(1)
    
    # Remove it
    content = content.replace(waitlist_html, '')
    
    # Put it right after ONBOARDING: CREAR CUENTA
    target = '<!-- Formulario de Acceso Desarrolladores (Devs) -->'
    content = content.replace(target, waitlist_html + '\n\n                ' + target)
    
    with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
        f.write(content)
        print("Success")
else:
    print("Match not found")
