import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# 1. Extract success container out of waitlist view and create beta view
# We'll just replace the entire onboarding block from ONBOARDING: CREAR CUENTA to the end of ONBOARDING: BETA WAITLIST with a new, well-structured set of views.

# Find the start of ONBOARDING: CREAR CUENTA
start_str = '<!-- ONBOARDING: CREAR CUENTA -->'
end_str = '<!-- Formulario de Acceso Desarrolladores (Devs) -->'

match = re.search(r'(<!-- ONBOARDING: CREAR CUENTA -->.*?)\s*<!-- Formulario de Acceso Desarrolladores \(Devs\) -->', content, re.DOTALL)
if match:
    old_onboarding_html = match.group(1)
    
    new_onboarding_html = """<!-- ONBOARDING: CREAR CUENTA (From Login) -->
                <div id="onboarding-register-view" class="auth-panel-content" style="display: none;">
                    <div class="auth-header-container">
                        <div class="auth-header">
                            <h2 class="welcome-title">Crea tu cuenta</h2>
                            <p class="welcome-subtitle">Algunas cosas para que revises</p>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 24px; background: #18181B; padding: 16px; border-radius: 8px; border: 1px solid #3F3F46; text-align: center;">
                        <p style="font-size: 14px; color: #A1A1AA; margin-bottom: 8px;">Email verificado como <strong id="onboarding-email-display" style="color: #FFFFFF;">usuario@gmail.com</strong></p>
                        <a href="#" onclick="showLoginView(); return false;" style="font-size: 13px; color: #A78BFA; text-decoration: none; font-weight: 500;">Usar un correo electrónico diferente</a>
                    </div>

                    <form id="onboarding-register-form">
                        <div class="input-group" style="flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 16px;">
                            <input type="checkbox" id="terms-check" required style="margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                            <label for="terms-check" style="font-size: 13px; line-height: 1.5; color: #D4D4D8; font-weight: 400; cursor: pointer;">
                                Acepto los términos y condiciones y política de uso aceptable de Innvisor y confirmo que tengo al menos 18 años de edad.
                            </label>
                        </div>
                        
                        <div class="input-group" style="flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 24px;">
                            <input type="checkbox" id="promo-check" style="margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                            <label for="promo-check" style="font-size: 13px; line-height: 1.5; color: #D4D4D8; font-weight: 400; cursor: pointer;">
                                Suscríbete para recibir correos promocionales, actualizaciones de producto y ofertas exclusivas de Bublee.
                            </label>
                        </div>

                        <button type="button" onclick="showWaitlistView()" class="btn btn-primary btn-block btn-login-submit" style="background-color: #FFFFFF; color: #18181B; border: none;">Crear Cuenta</button>
                    </form>
                </div>

                <!-- ONBOARDING: BETA WAITLIST (Continuation of Login) -->
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

                            <button type="button" onclick="showSuccessView('onboarding-waitlist-view')" class="btn btn-primary btn-block btn-login-submit" style="background-color: #FFFFFF; color: #18181B; border: none;">Hacer Fila</button>
                        </form>
                    </div>
                </div>

                <!-- ONBOARDING: JOIN BETA DIRECTLY (From "No account") -->
                <div id="onboarding-join-beta-view" class="auth-panel-content" style="display: none;">
                    <div class="auth-header-container">
                        <div class="auth-header">
                            <h2 class="welcome-title">Solicitar Acceso Beta</h2>
                            <p class="welcome-subtitle">Ingresa tus datos para unirte a la lista de espera de Bublee.</p>
                        </div>
                    </div>
                    <form id="beta-signup-form">
                        <div class="input-group">
                            <label>Correo Electrónico</label>
                            <input type="email" id="beta-email" required placeholder="correo@empresa.com">
                        </div>
                        <div class="input-group">
                            <label>Nombre Completo</label>
                            <input type="text" id="beta-name" required placeholder="Tu nombre">
                        </div>
                        <div class="input-group" style="flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 24px; margin-top: 16px;">
                            <input type="checkbox" id="beta-terms" required style="margin-top: 4px; width: 18px; height: 18px; cursor: pointer;">
                            <label for="beta-terms" style="font-size: 13px; line-height: 1.5; color: #D4D4D8; font-weight: 400; cursor: pointer;">
                                Acepto los términos y condiciones y política de uso aceptable de Innvisor y confirmo que tengo al menos 18 años.
                            </label>
                        </div>
                        <button type="button" onclick="completeBetaSignup()" class="btn btn-primary btn-block btn-login-submit" style="background-color: #FFFFFF; color: #18181B; border: none;">Hacer Fila</button>
                        
                        <div style="text-align: center; margin-top: 24px;">
                            <a href="#" onclick="showLoginView(); return false;" class="login-secondary-link back-link">Volver al inicio de sesión</a>
                        </div>
                    </form>
                </div>

                <!-- ONBOARDING: SUCCESS -->
                <div id="onboarding-success-view" class="auth-panel-content" style="display: none; text-align: center; padding: 32px 0;">
                    <i data-lucide="check-circle" size="56" style="color: #10B981; margin-bottom: 24px;"></i>
                    <h3 class="welcome-title" style="margin-bottom: 12px;">¡Estás en la lista!</h3>
                    <p class="welcome-subtitle" style="margin-bottom: 32px;">Te avisaremos por correo electrónico si eres apto para ingresar al Modo Beta.</p>
                    <a href="/" style="display: inline-block; padding: 12px 24px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #FFFFFF; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s;">Volver al inicio</a>
                </div>
"""
    content = content.replace(old_onboarding_html, new_onboarding_html)


# 2. Update the javascript
js_regex = r'<script>\s*// Onboarding Flow Logic.*?</script>'
match_js = re.search(js_regex, content, re.DOTALL)
if match_js:
    new_js = """<script>
        // Onboarding Flow Logic
        
        // Scenario A: From Login Form (User typed email but not registered)
        function startOnboarding(email) {
            document.getElementById('standard-login-view').classList.remove('active');
            document.getElementById('standard-login-view').style.display = 'none';
            document.getElementById('auth-mode-toggle-container').style.display = 'none';
            
            const registerView = document.getElementById('onboarding-register-view');
            registerView.style.display = 'block';
            setTimeout(() => registerView.classList.add('active'), 10);
            
            if(email) {
                document.getElementById('onboarding-email-display').textContent = email;
            } else {
                let inputEmail = document.getElementById('login-email').value;
                if(inputEmail) {
                    document.getElementById('onboarding-email-display').textContent = inputEmail;
                } else {
                    document.getElementById('onboarding-email-display').textContent = 'usuario@gmail.com';
                }
            }
        }

        // Scenario B: From "No account? Register" Link (Direct Beta Request)
        function startBetaSignup() {
            document.getElementById('standard-login-view').classList.remove('active');
            document.getElementById('standard-login-view').style.display = 'none';
            document.getElementById('auth-mode-toggle-container').style.display = 'none';
            
            const betaView = document.getElementById('onboarding-join-beta-view');
            betaView.style.display = 'block';
            setTimeout(() => betaView.classList.add('active'), 10);
        }

        function showLoginView() {
            document.getElementById('onboarding-register-view').classList.remove('active');
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').classList.remove('active');
            document.getElementById('onboarding-waitlist-view').style.display = 'none';
            document.getElementById('onboarding-join-beta-view').classList.remove('active');
            document.getElementById('onboarding-join-beta-view').style.display = 'none';
            document.getElementById('onboarding-success-view').classList.remove('active');
            document.getElementById('onboarding-success-view').style.display = 'none';
            
            const loginView = document.getElementById('standard-login-view');
            loginView.style.display = 'block';
            setTimeout(() => loginView.classList.add('active'), 10);
            
            document.getElementById('auth-mode-toggle-container').style.display = 'block';
        }

        // Continuation of Scenario A
        function showWaitlistView() {
            if(!document.getElementById('terms-check').checked) {
                alert("Debes aceptar los términos y condiciones de Innvisor para continuar.");
                return;
            }
            document.getElementById('onboarding-register-view').classList.remove('active');
            document.getElementById('onboarding-register-view').style.display = 'none';
            
            const waitlistView = document.getElementById('onboarding-waitlist-view');
            waitlistView.style.display = 'block';
            setTimeout(() => waitlistView.classList.add('active'), 10);
        }

        // Finishing Scenario B
        function completeBetaSignup() {
            if(!document.getElementById('beta-email').value || !document.getElementById('beta-name').value) {
                alert("Por favor ingresa tu correo y nombre.");
                return;
            }
            if(!document.getElementById('beta-terms').checked) {
                alert("Debes aceptar los términos y condiciones de Innvisor para continuar.");
                return;
            }
            showSuccessView('onboarding-join-beta-view');
        }

        // Universal Success View
        function showSuccessView(fromViewId) {
            if(fromViewId === 'onboarding-waitlist-view' && !document.getElementById('waitlist-name').value) {
                alert("Por favor ingresa tu nombre.");
                return;
            }
            
            document.getElementById(fromViewId).classList.remove('active');
            document.getElementById(fromViewId).style.display = 'none';
            
            const successView = document.getElementById('onboarding-success-view');
            successView.style.display = 'block';
            setTimeout(() => successView.classList.add('active'), 10);
            
            if(typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }

        // Intercept standard login submit for demo purposes (Scenario A trigger)
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('email-check-form');
            if(loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    startOnboarding();
                });
            }
        });
    </script>"""
    content = content.replace(match_js.group(0), new_js)

# 3. Change the register link to trigger startBetaSignup()
content = content.replace('onclick="startOnboarding(); return false;">¿No tienes cuenta? Regístrate</a>', 'onclick="startBetaSignup(); return false;">¿No tienes cuenta? Regístrate</a>')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

