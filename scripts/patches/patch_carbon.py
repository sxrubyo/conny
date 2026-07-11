with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    css = f.read()

import re

# Remove the previously forced light theme block
css = re.sub(r'/\* FORCE LIGHT THEME FOR LOGIN \*/.*?(?=\Z|/\*|\n\n)', '', css, flags=re.DOTALL)

# Add the new Carbon Dark theme rules
carbon_theme = """
/* FORCE CARBON DARK THEME FOR LOGIN */
.login-right-side { 
    background-color: #18181B !important; /* Carbon dark background */
}
.login-form-wrapper { 
    background: #27272A !important; /* Slightly lighter charcoal card */
    border: 1px solid rgba(255,255,255,0.08) !important; 
    box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important; 
}
.welcome-title, .login-mobile-title { color: #FFFFFF !important; }
.welcome-subtitle { color: #A1A1AA !important; }
.input-group label { color: #D4D4D8 !important; }
.input-group input, .input-group select { 
    background-color: #18181B !important; 
    border-color: #3F3F46 !important; 
    color: #FFFFFF !important; 
}
.input-group input:focus, .input-group select:focus { 
    border-color: #A78BFA !important; 
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important; 
}
.login-divider::before, .login-divider::after { background-color: #3F3F46 !important; }
.login-divider span { color: #A1A1AA !important; }
.btn-google-login { 
    background-color: #18181B !important; 
    border-color: #3F3F46 !important; 
    color: #E4E4E7 !important; 
}
.btn-google-login:hover { background-color: #27272A !important; border-color: #52525B !important; }
.login-secondary-link { color: #A1A1AA !important; }
.login-secondary-link:hover { color: #FFFFFF !important; }
.login-mobile-logo { filter: brightness(0) invert(1) !important; /* White logo */ }

/* Onboarding specific text colors for dark theme */
#onboarding-register-view p, #onboarding-waitlist-view p { color: #A1A1AA !important; }
#onboarding-register-view strong { color: #FFFFFF !important; }
#onboarding-register-view div[style*="background: #F3F4F6"] { 
    background: #18181B !important; 
    border-color: #3F3F46 !important; 
}
#onboarding-register-view label { color: #D4D4D8 !important; }
#waitlist-success-container h3 { color: #FFFFFF !important; }
"""

css += "\n" + carbon_theme

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(css)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Bump CSS version
content = content.replace('app.css?v=11', 'app.css?v=12')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)
