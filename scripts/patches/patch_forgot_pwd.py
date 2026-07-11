with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    html = f.read()

old_pwd = """                                <div class="input-group">
                                    <label for="login-password">Contraseña</label>
                                    <input type="password" id="login-password" required placeholder="contraseña">
                                </div>"""

new_pwd = """                                <div class="input-group">
                                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                                        <label for="login-password" style="margin-bottom: 0;">Contraseña</label>
                                        <a href="#" onclick="alert('Te hemos enviado un enlace para recuperar tu contraseña.'); return false;" style="font-size: 13px; color: #A1A1AA; text-decoration: none;">¿Olvidaste tu contraseña?</a>
                                    </div>
                                    <input type="password" id="login-password" required placeholder="contraseña" style="margin-top: 8px;">
                                </div>"""

html = html.replace(old_pwd, new_pwd)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(html)
