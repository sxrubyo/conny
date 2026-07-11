import re

# 1. FIX JAVASCRIPT IN HTML
with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Remove the intercept block
intercept_regex = r'\s*// Intercept standard login submit for demo purposes.*?}\);'
content = re.sub(intercept_regex, '', content, flags=re.DOTALL)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)


# 2. FIX CSS FOR MOBILE
with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

mobile_css = """
/* ABSOLUTE MOBILE OVERRIDES FOR CARBON THEME */
@media (max-width: 600px) {
    body #login-screen .login-form-wrapper {
        padding: 32px 24px !important; /* Reduce padding for mobile */
        max-width: 100% !important;
        margin: 0 16px !important; /* Give it a little outer margin so it's not edge-to-edge */
        border-radius: 16px !important;
    }
    
    body #login-screen .login-right-side {
        padding: 0 !important;
    }
}
"""

css += "\n" + mobile_css

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

# Bump CSS version again
with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()
content = content.replace('app.css?v=15', 'app.css?v=16')
with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

