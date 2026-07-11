import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    html = f.read()

# Add link for "No tienes una cuenta? Unete a la lista beta" under the login button
beta_link_html = """
                                <button type="submit" class="btn btn-primary btn-block btn-login-submit">Iniciar sesión</button>
                                <div style="text-align: center; margin-top: 16px;">
                                    <span style="color: #6b7280; font-size: 13px;">¿No tienes una cuenta? </span>
                                    <a href="#" id="show-beta-form" style="color: #a78bfa; font-size: 13px; text-decoration: none; font-weight: 600;">Únete a la lista beta</a>
                                </div>
"""

# Replace the login button to insert the link below it
html = re.sub(r'<button type="submit" class="btn btn-primary btn-block btn-login-submit">Iniciar sesión</button>', beta_link_html, html)

# Add Beta waitlist form (hidden by default)
beta_form_html = """
                        <!-- Beta Waitlist View -->
                        <div id="step-beta-view" style="display: none;">
                            <form id="beta-waitlist-form">
                                <h3 style="color: white; margin-bottom: 8px;">Lista Beta</h3>
                                <p style="color: #6b7280; font-size: 13px; margin-bottom: 24px;">Ingresa tu correo y te contactaremos cuando abramos nuevos cupos.</p>
                                
                                <div class="input-group">
                                    <label for="beta-email">Correo electrónico</label>
                                    <input type="email" id="beta-email" required placeholder="correo@empresa.com">
                                </div>
                                
                                <div id="beta-success-msg" style="display: none; padding: 12px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; color: #10b981; font-size: 13px; margin-bottom: 16px; text-align: center;">
                                    ¡Gracias! Te hemos añadido a la lista beta.
                                </div>
                                
                                <button type="submit" id="btn-beta-submit" class="btn btn-primary btn-block btn-login-submit" style="margin-bottom: 12px;">Ingresar a la lista</button>
                                <a href="#" id="btn-back-to-login" class="login-secondary-link back-link" style="display: block; text-align: center; margin-top: 16px; color: #a1a1aa; text-decoration: none; font-size: 13px;">Volver a iniciar sesión</a>
                            </form>
                        </div>
"""

# Insert beta form right after step-token-direct-view
html = html.replace('<!-- Paso 2: Contraseña (Usuario Existente) -->', beta_form_html + '\n                        <!-- Paso 2: Contraseña (Usuario Existente) -->')

# Let's fix mobile responsiveness of the login box
html = html.replace('width: 100%; max-width: 440px;', 'width: 100%; max-width: 440px; box-sizing: border-box;')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(html)
print("Updated index.html")
