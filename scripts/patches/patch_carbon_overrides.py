with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

# Add an absolute override at the very end of the file with crazy specificity
absolute_overrides = """
/* ABSOLUTE CARBON OVERRIDES */
body #login-screen .login-right-side .welcome-title,
body #login-screen .login-right-side .login-mobile-title { 
    color: #FFFFFF !important; 
}

body #login-screen .login-right-side .login-mobile-logo {
    filter: brightness(0) invert(1) !important;
}
"""

css += "\n" + absolute_overrides

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Bump CSS version
content = content.replace('app.css?v=13', 'app.css?v=14')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

