with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

js = js.replace("const tabDevRegister = document.getElementById('tab-dev-register');", "")
js = js.replace("const tabDevLogin = document.getElementById('tab-dev-login');", "")

declarations = """
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const tabDevRegister = document.getElementById('tab-dev-register');
const tabDevLogin = document.getElementById('tab-dev-login');
"""
js = js.replace("const btnSwitchToDev = document.getElementById('btn-switch-to-dev');", declarations)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
