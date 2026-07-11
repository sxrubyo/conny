import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Remove Bublee text
content = content.replace('<h1 class="login-mobile-title">Bublee.</h1>', '')

# Bump CSS version again
content = content.replace('app.css?v=8', 'app.css?v=9')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

# Make the card less "alargada" (reduce padding and width slightly)
css = css.replace("max-width: 400px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 48px 40px;", "max-width: 380px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 40px 32px;")

# Eliminate dark theme for login completely by overriding it heavily to light
# We will just append a massive override block that forces light colors even in dark-theme
force_light = """
/* FORCE LIGHT THEME FOR LOGIN */
body.dark-theme .login-right-side { background-color: #F9FAFB !important; }
body.dark-theme .login-form-wrapper { background: #FFFFFF !important; border: 1px solid rgba(0,0,0,0.08) !important; box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important; }
body.dark-theme .welcome-title { color: #111827 !important; }
body.dark-theme .welcome-subtitle { color: #6B7280 !important; }
body.dark-theme .input-group label { color: #374151 !important; }
body.dark-theme .input-group input { background-color: #FFFFFF !important; border-color: #D1D5DB !important; color: #111827 !important; }
body.dark-theme .input-group input:focus { border-color: #6366F1 !important; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important; }
body.dark-theme .login-divider::before, body.dark-theme .login-divider::after { background-color: #E5E7EB !important; }
body.dark-theme .login-divider span { color: #9CA3AF !important; }
body.dark-theme .btn-google-login { background-color: #FFFFFF !important; border-color: #E5E7EB !important; color: #374151 !important; }
body.dark-theme .btn-google-login:hover { background-color: #F9FAFB !important; }
body.dark-theme .login-secondary-link { color: #6B7280 !important; }
body.dark-theme .login-secondary-link:hover { color: #111827 !important; }
"""
css += "\n" + force_light

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

