with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Add missing DOM declarations right after `const loginScreen`
missing = """
const developerLoginView = document.getElementById('developer-login-view');
const standardLoginView = document.getElementById('standard-login-view');
"""
js = js.replace("const loginScreen = document.getElementById('login-screen');", "const loginScreen = document.getElementById('login-screen');" + missing)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
