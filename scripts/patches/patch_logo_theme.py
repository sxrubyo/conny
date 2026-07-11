import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

# Add smart filters for the logo
smart_logo_css = """
/* Smart Logo Contrast for Login and App */
/* In Light Mode (White backgrounds) -> Logo must be Black */
.login-mobile-logo, .placeholder-isotype-img {
    filter: brightness(0) !important; /* Force black */
}

/* In Dark Mode (Black backgrounds) -> Logo must be White */
body.dark-theme .login-mobile-logo, body.dark-theme .placeholder-isotype-img {
    filter: brightness(0) invert(1) !important; /* Force white */
}

/* Wait, since the login screen is forced to light background ALWAYS now, 
   we should force the login logo to ALWAYS be black so it's visible. */
.login-right-side .login-mobile-logo {
    filter: brightness(0) !important; 
}
"""
css += "\n" + smart_logo_css

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Bump CSS version again
content = content.replace('app.css?v=9', 'app.css?v=10')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

