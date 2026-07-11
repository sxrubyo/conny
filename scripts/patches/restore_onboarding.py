import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Remove the broken pieces
content = re.sub(r'<!-- ONBOARDING: CREAR CUENTA -->.*?</div>\s*</div>', '', content, flags=re.DOTALL)
content = re.sub(r'<!-- ONBOARDING: BETA WAITLIST -->.*?</div>\s*</div>', '', content, flags=re.DOTALL)

# Re-inject them properly
full_views = """
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

target = '<!-- Formulario de Acceso Desarrolladores (Devs) -->'
content = content.replace(target, full_views + '\n\n                ' + target)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)
