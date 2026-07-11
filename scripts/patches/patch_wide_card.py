import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

# 1. Make the card wider
css = css.replace('max-width: 380px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 40px 32px;', 'max-width: 480px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 48px 40px;')
# Also check if it was max-width 400px
css = css.replace('max-width: 400px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 48px 40px;', 'max-width: 480px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 48px 40px;')

# 2. Add rule for API Access to be white
carbon_addition = """
.dev-switch-link { color: #FFFFFF !important; opacity: 0.8; }
.dev-switch-link:hover { opacity: 1; }
"""
css += "\n" + carbon_addition

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Bump CSS version
content = content.replace('app.css?v=12', 'app.css?v=13')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)
