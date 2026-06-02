import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Quitar las pestañas de Login/Registro de dev
dev_tabs_regex = r'<!-- Selector de Pestañas Dev \(Login / Registro\) -->\s*<div class="dev-tabs".*?</div>'
html = re.sub(dev_tabs_regex, "", html, flags=re.DOTALL)

# Quitar la seccion de registro de dev
dev_reg_regex = r'<!-- Tab: Registrar Cuenta Dev -->\s*<div id="dev-register-tab-content".*?</div>\s*<!--'
html = re.sub(dev_reg_regex, "<!--", html, flags=re.DOTALL)

# Cambiar "Conny Dev." a un estilo más profesional
old_header = """<div class="auth-header">
                        <h2 class="welcome-title">Conny Dev.</h2>
                        <p class="welcome-subtitle">Portal de Desarrollo</p>
                    </div>"""

new_header = """<div class="auth-header" style="text-align: center; margin-bottom: 30px;">
                        <div style="width: 48px; height: 48px; background: rgba(139, 92, 246, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; border: 1px solid rgba(139, 92, 246, 0.3);">
                            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                        </div>
                        <h2 class="welcome-title" style="color: #f3f4f6; font-size: 24px; font-weight: 700;">Developer Console</h2>
                        <p class="welcome-subtitle" style="color: #9ca3af; font-size: 14px;">Acceso restringido. Utiliza el CLI de Conny para generar credenciales.</p>
                    </div>"""
html = html.replace(old_header, new_header)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
