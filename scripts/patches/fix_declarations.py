import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# remove bottom declarations
js = js.replace("const btnSwitchToDev = document.getElementById('btn-switch-to-dev');", "")
js = js.replace("const tabDevRegister = document.getElementById('tab-dev-register');", "")
js = js.replace("const tabDevLogin = document.getElementById('tab-dev-login');", "")
js = js.replace("const btnBackToAdmin = document.getElementById('btn-back-to-admin');", "")

declarations = """
// --- Added missing dev view elements at top ---
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const tabDevRegister = document.getElementById('tab-dev-register');
const tabDevLogin = document.getElementById('tab-dev-login');
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
// ----------------------------------------------
"""
js = js.replace("// State Management", declarations + "\n// State Management")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
