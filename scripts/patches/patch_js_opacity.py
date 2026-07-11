import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Fix JS to manage the .active class properly instead of just display
old_js = """        function startOnboarding(email) {
            document.getElementById('standard-login-view').style.display = 'none';
            document.getElementById('auth-mode-toggle-container').style.display = 'none';
            document.getElementById('onboarding-register-view').style.display = 'block';"""

new_js = """        function startOnboarding(email) {
            document.getElementById('standard-login-view').classList.remove('active');
            document.getElementById('standard-login-view').style.display = 'none';
            document.getElementById('auth-mode-toggle-container').style.display = 'none';
            
            const registerView = document.getElementById('onboarding-register-view');
            registerView.style.display = 'block';
            setTimeout(() => registerView.classList.add('active'), 10);"""

content = content.replace(old_js, new_js)

old_js2 = """        function showLoginView() {
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').style.display = 'none';
            document.getElementById('standard-login-view').style.display = 'block';
            document.getElementById('auth-mode-toggle-container').style.display = 'block';
        }"""

new_js2 = """        function showLoginView() {
            document.getElementById('onboarding-register-view').classList.remove('active');
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').classList.remove('active');
            document.getElementById('onboarding-waitlist-view').style.display = 'none';
            
            const loginView = document.getElementById('standard-login-view');
            loginView.style.display = 'block';
            setTimeout(() => loginView.classList.add('active'), 10);
            
            document.getElementById('auth-mode-toggle-container').style.display = 'block';
        }"""
content = content.replace(old_js2, new_js2)

old_js3 = """        function showWaitlistView() {
            // Check terms
            if(!document.getElementById('terms-check').checked) {
                alert("Debes aceptar los términos y condiciones para continuar.");
                return;
            }
            document.getElementById('onboarding-register-view').style.display = 'none';
            document.getElementById('onboarding-waitlist-view').style.display = 'block';
            lucide.createIcons();
        }"""

new_js3 = """        function showWaitlistView() {
            // Check terms
            if(!document.getElementById('terms-check').checked) {
                alert("Debes aceptar los términos y condiciones para continuar.");
                return;
            }
            document.getElementById('onboarding-register-view').classList.remove('active');
            document.getElementById('onboarding-register-view').style.display = 'none';
            
            const waitlistView = document.getElementById('onboarding-waitlist-view');
            waitlistView.style.display = 'block';
            setTimeout(() => waitlistView.classList.add('active'), 10);
            
            lucide.createIcons();
        }"""
content = content.replace(old_js3, new_js3)

# While we're here, let's fix the text "Bublee" color in the mobile header which might still have color: #111827 from my inline style earlier!
content = content.replace('color: #111827; letter-spacing: -0.02em; margin: 0;">Bublee</h1>', 'color: #FFFFFF; letter-spacing: -0.02em; margin: 0;">Bublee</h1>')

# Bump CSS just in case
content = content.replace('app.css?v=14', 'app.css?v=15')

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

