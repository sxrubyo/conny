import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# 1. Restore the Bublee text next to the logo in the auth header
old_mobile_header = """                <div class="login-mobile-header">
                    <img src="/isotype" alt="Bublee Logo" class="login-mobile-logo" onerror="this.src='/logo'">
                    
                </div>"""
new_mobile_header = """                <div class="login-mobile-header" style="flex-direction: row; gap: 12px;">
                    <img src="/isotype" alt="Bublee Logo" class="login-mobile-logo" onerror="this.src='/logo'" style="margin-bottom: 0;">
                    <h1 class="login-mobile-title" style="font-size: 24px; font-weight: 700; color: #111827; letter-spacing: -0.02em; margin: 0;">Bublee</h1>
                </div>"""
if '<h1 class="login-mobile-title">Bublee.</h1>' not in content:
    content = content.replace(old_mobile_header, new_mobile_header)

# If the old replace failed, let's just do a regex
content = re.sub(
    r'<div class="login-mobile-header">.*?</div>',
    new_mobile_header,
    content,
    flags=re.DOTALL
)

# 2. Inject the new views
# The current standard-login-view ends around line 125, before the </template> or before the </div> of login-form-wrapper
# Let's find the closing tag of standard-login-view.
# It's followed by <!-- Modal para Magic Link --> or <!-- Pantalla del Sistema Bublee -->
# I will append the new views immediately after `standard-login-view`.

new_views = """
                <!-- ONBOARDING: CREAR CUENTA -->
                <div id="onboarding-register-view" class="auth-panel-content" style="display: none;">
                    <div class="auth-header-container">
                        <div class="auth-header">
                            <h2 class="welcome-title">Crea tu cuenta</h2>
                            <p class="welcome-subtitle">Algunas cosas para que revises</p>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 24px; background: #F3F4F6; padding: 16px; border-radius: 8px; border: 1px solid #E5E7EB; text-align: center;">
                        <p style="font-size: 14px; color: #374151; margin-bottom: 8px;">Email verificado como <strong id="onboarding-email-display">usuario@gmail.com</strong></p>
                        <a href="#" onclick="showLoginView(); return false;" style="font-size: 13px; color: #6366F1; text-decoration: none; font-weight: 500;">Usar un correo electrónico diferente</a>
                    </div>

                    <form id="onboarding-register-form">
                        <div class="input-group" style="flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 16px;">
                            <input type="checkbox" id="terms-check" required style="margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                            <label for="terms-check" style="font-size: 13px; line-height: 1.5; color: #4B5563; font-weight: 400; cursor: pointer;">
                                Acepto los términos y condiciones y política de uso aceptable de Innvisor y confirmo que tengo al menos 18 años de edad.
                            </label>
                        </div>
                        
                        <div class="input-group" style="flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 24px;">
                            <input type="checkbox" id="promo-check" style="margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                            <label for="promo-check" style="font-size: 13px; line-height: 1.5; color: #4B5563; font-weight: 400; cursor: pointer;">
                                Suscríbete para recibir correos promocionales, actualizaciones de producto y ofertas exclusivas de Bublee.
                            </label>
                        </div>

                        <button type="button" onclick="showWaitlistView()" class="btn btn-primary btn-block btn-login-submit" style="background-color: #111827; color: white;">Crear Cuenta</button>
                    </form>
                </div>

                <!-- ONBOARDING: BETA WAITLIST -->
                <div id="onboarding-waitlist-view" class="auth-panel-content" style="display: none;">
                    <div class="auth-header-container">
                        <div class="auth-header">
                            <h2 class="welcome-title">Planes de Pago y Modo Beta</h2>
                            <p class="welcome-subtitle">Únete a la lista de espera para acceso anticipado.</p>
                        </div>
                    </div>

                    <div id="waitlist-form-container">
                        <form id="onboarding-waitlist-form">
                            <div class="input-group">
                                <label for="waitlist-name">Nombre completo</label>
                                <input type="text" id="waitlist-name" required placeholder="Tu nombre">
                            </div>
                            <div class="input-group">
                                <label for="waitlist-company">Empresa (Opcional)</label>
                                <input type="text" id="waitlist-company" placeholder="Nombre de tu agencia o empresa">
                            </div>

                            <button type="button" onclick="completeWaitlist()" class="btn btn-primary btn-block btn-login-submit" style="background-color: #111827; color: white;">Hacer Fila</button>
                        </form>
                    </div>

                    <div id="waitlist-success-container" style="display: none; text-align: center; padding: 32px 0;">
                        <i data-lucide="check-circle" size="48" style="color: #10B981; margin-bottom: 16px;"></i>
                        <h3 style="font-size: 20px; color: #111827; margin-bottom: 8px;">¡Estás en la lista!</h3>
                        <p style="font-size: 15px; color: #4B5563;">Te avisaremos por correo electrónico si eres apto para ingresar al Modo Beta.</p>
                        <a href="/" style="display: inline-block; margin-top: 24px; color: #6366F1; text-decoration: none; font-size: 14px; font-weight: 500;">Volver al inicio</a>
                    </div>
                </div>
"""

# Inject after standard-login-view
# We need to find the end of standard-login-view. 
# It ends at `<div id="auth-mode-toggle-container">` which toggles register/login.
# Actually, let's just insert it before `<div id="auth-mode-toggle-container">`
content = content.replace('                    <div id="auth-mode-toggle-container"', new_views + '\n                    <div id="auth-mode-toggle-container"')

# 3. Add the javascript functions to handle the flow
js_functions = """
    <script>
        // Onboarding Flow Logic
        function startOnboarding(email) {
            document.getElementById('standard-login-view').style.display = 'none';
            document.getElementById('auth-mode-toggle-container').style.display = 'none';
            document.getElementById('onboarding-register-view').style.display = 'block';
            
            if(email) {
                document.getElementById('onboarding-email-display').textContent = email;
            } else {
                let inputEmail = document.getElementById('login-email').value;
                if(inputEmail) {
                    document.getElementById('onboarding-email-display').textContent = inputEmail;
                }
            }
        }

        function showLoginView() {
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').style.display = 'none';
            document.getElementById('standard-login-view').style.display = 'block';
            document.getElementById('auth-mode-toggle-container').style.display = 'block';
        }

        function showWaitlistView() {
            // Check terms
            if(!document.getElementById('terms-check').checked) {
                alert("Debes aceptar los términos y condiciones para continuar.");
                return;
            }
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').style.display = 'block';
            lucide.createIcons();
        }

        function completeWaitlist() {
            if(!document.getElementById('waitlist-name').value) {
                alert("Por favor ingresa tu nombre.");
                return;
            }
            document.getElementById('waitlist-form-container').style.display = 'none';
            document.getElementById('waitlist-success-container').style.display = 'block';
        }

        // Intercept standard login submit for demo purposes
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('email-check-form');
            if(loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    startOnboarding();
                });
            }
        });
    </script>
</body>
"""
content = content.replace('</body>', js_functions)

# Also ensure "auth-mode-toggle-container" is modified to trigger onboarding
content = content.replace('<a href="#" class="login-secondary-link register-link">Regístrate</a>', '<a href="#" class="login-secondary-link register-link" onclick="startOnboarding(\'nuevo@usuario.com\'); return false;">Crear cuenta nueva</a>')

# Bump CSS Version
content = content.replace('app.css?v=10', 'app.css?v=11')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)
