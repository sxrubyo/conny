with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    html = f.read()

# Replace the login password input with a wrapped version containing the eye icon
old_input = '<input type="password" id="login-password" required placeholder="contraseña" style="margin-top: 8px;">'
new_input = '''<div style="position: relative; margin-top: 8px;">
                                        <input type="password" id="login-password" required placeholder="contraseña" style="width: 100%; box-sizing: border-box; padding-right: 40px;">
                                        <button type="button" id="toggle-password" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; padding: 0; cursor: pointer; color: #a1a1aa; display: flex; align-items: center; justify-content: center;">
                                            <i data-lucide="eye" style="width: 20px; height: 20px;"></i>
                                        </button>
                                    </div>'''

html = html.replace(old_input, new_input)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(html)
