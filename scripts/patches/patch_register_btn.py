import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

old_link = '<a href="#" id="btn-switch-to-register" class="register-link">¿No tienes cuenta? Regístrate</a>'
new_link = '<a href="#" id="btn-switch-to-register" class="register-link" onclick="startOnboarding(); return false;">¿No tienes cuenta? Regístrate</a>'

content = content.replace(old_link, new_link)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

