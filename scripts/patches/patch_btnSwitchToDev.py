with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# Remove the one at line 3133
js = js.replace("const btnSwitchToDev = document.getElementById('btn-switch-to-dev');", "")

# Add it to the top declarations block
declarations = """
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
"""
js = js.replace("const btnBackToAdmin = document.getElementById('btn-back-to-admin');", declarations)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
