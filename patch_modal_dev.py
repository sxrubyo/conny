import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# 1. Quitar el developer-login-view del auth-panel principal
regex_auth_dev = r'<!-- Formulario de Acceso Desarrolladores \(Devs\) -->\s*<div id="developer-login-view" class="auth-panel-content" style="display: none;">.*?(?=</div>\s*</div>\s*<!-- Panel Gráfico Derecho -->)'
match = re.search(regex_auth_dev, html, flags=re.DOTALL)
if match:
    # Eliminamos esto del panel de auth
    html = html.replace(match.group(0), "")

# 2. Agregar el modal al final del body o cerca del final
modal_html = """
    <!-- Modal de Acceso para Devs -->
    <div id="dev-login-modal" class="modal-overlay" style="display: none; align-items: center; justify-content: center; z-index: 9999;">
        <div class="modal-content" style="max-width: 420px; width: 100%; background: #1a1625; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 32px; box-shadow: 0 0 0 transparent;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: rgba(139, 92, 246, 0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(139, 92, 246, 0.3);">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                    </div>
                    <div>
                        <h2 style="color: #f3f4f6; font-size: 20px; font-weight: 700; margin: 0;">Conny Dev</h2>
                        <p style="color: #9ca3af; font-size: 13px; margin: 2px 0 0 0;">Portal de Desarrollo</p>
                    </div>
                </div>
                <button type="button" id="btn-close-dev-modal" style="background: none; border: none; color: #9ca3af; cursor: pointer; padding: 4px;">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
            </div>
            
            <div class="dev-tabs" style="display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">
                <button type="button" id="tab-dev-login" class="dev-tab active" style="background: transparent; border: none; color: #a78bfa; font-weight: 600; cursor: pointer; padding: 4px 8px; font-size: 14px;">Iniciar Sesión</button>
                <button type="button" id="tab-dev-register" class="dev-tab" style="background: transparent; border: none; color: #6b7280; font-weight: 600; cursor: pointer; padding: 4px 8px; font-size: 14px;">Registrarse</button>
            </div>

            <div id="dev-login-tab-content">
                <form id="dev-login-form-new">
                    <div class="input-group" style="margin-bottom: 16px;">
                        <label for="dev-login-email" style="display: block; color: #d1d5db; font-size: 13px; margin-bottom: 6px;">Correo de Desarrollador</label>
                        <input type="email" id="dev-login-email" required placeholder="correo@dev.com" style="width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none;">
                    </div>
                    <div class="input-group" style="margin-bottom: 24px;">
                        <label for="dev-login-password" style="display: block; color: #d1d5db; font-size: 13px; margin-bottom: 6px;">Contraseña</label>
                        <input type="password" id="dev-login-password" required placeholder="Tu contraseña" style="width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none;">
                    </div>
                    <p id="dev-login-error" style="color: #ef4444; font-size: 13px; margin: -10px 0 16px 0; min-height: 18px;"></p>
                    <button type="submit" class="btn btn-primary" style="width: 100%; border-radius: 8px; padding: 12px; font-weight: 600;">Entrar como Dev</button>
                </form>
            </div>

            <div id="dev-register-tab-content" style="display: none;">
                <form id="dev-register-form">
                    <div class="input-group" style="margin-bottom: 16px;">
                        <label for="dev-reg-email" style="display: block; color: #d1d5db; font-size: 13px; margin-bottom: 6px;">Correo Nuevo</label>
                        <input type="email" id="dev-reg-email" required placeholder="correo@dev.com" style="width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none;">
                    </div>
                    <div class="input-group" style="margin-bottom: 16px;">
                        <label for="dev-reg-password" style="display: block; color: #d1d5db; font-size: 13px; margin-bottom: 6px;">Contraseña Segura</label>
                        <input type="password" id="dev-reg-password" required placeholder="Crea una contraseña" style="width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none;">
                    </div>
                    <div class="input-group" style="margin-bottom: 24px;">
                        <label for="dev-reg-token" style="display: block; color: #d1d5db; font-size: 13px; margin-bottom: 6px;">Token Maestro (Autorización)</label>
                        <input type="password" id="dev-reg-token" required placeholder="Pídelo al Admin Principal" style="width: 100%; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none;">
                    </div>
                    <p id="dev-reg-error" style="color: #ef4444; font-size: 13px; margin: -10px 0 16px 0; min-height: 18px;"></p>
                    <button type="submit" class="btn btn-primary" style="width: 100%; border-radius: 8px; padding: 12px; font-weight: 600;">Registrar Cuenta Dev</button>
                </form>
            </div>
        </div>
    </div>
"""

idx_body_end = html.rfind('</body>')
if idx_body_end != -1:
    html = html[:idx_body_end] + modal_html + html[idx_body_end:]

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)

