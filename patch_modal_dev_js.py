with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

import re

# Remove old dev login button logic
old_logic_regex = r'const btnSwitchToDev.*?\}\);'
js = re.sub(old_logic_regex, "", js, flags=re.DOTALL)

# Add new modal logic
modal_js = """
// Dev Login Modal Logic
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const devLoginModal = document.getElementById('dev-login-modal');
const btnCloseDevModal = document.getElementById('btn-close-dev-modal');

const tabDevLogin = document.getElementById('tab-dev-login');
const tabDevRegister = document.getElementById('tab-dev-register');
const devLoginTabContent = document.getElementById('dev-login-tab-content');
const devRegisterTabContent = document.getElementById('dev-register-tab-content');

if (btnSwitchToDev && devLoginModal) {
    btnSwitchToDev.addEventListener('click', (e) => {
        e.preventDefault();
        devLoginModal.style.display = 'flex';
    });
}

if (btnCloseDevModal && devLoginModal) {
    btnCloseDevModal.addEventListener('click', () => {
        devLoginModal.style.display = 'none';
    });
    // Close on click outside
    devLoginModal.addEventListener('click', (e) => {
        if(e.target === devLoginModal) devLoginModal.style.display = 'none';
    });
}

if (tabDevLogin && tabDevRegister) {
    tabDevLogin.addEventListener('click', () => {
        tabDevLogin.style.color = '#a78bfa';
        tabDevRegister.style.color = '#6b7280';
        devLoginTabContent.style.display = 'block';
        devRegisterTabContent.style.display = 'none';
    });
    tabDevRegister.addEventListener('click', () => {
        tabDevRegister.style.color = '#a78bfa';
        tabDevLogin.style.color = '#6b7280';
        devRegisterTabContent.style.display = 'block';
        devLoginTabContent.style.display = 'none';
    });
}

const devLoginFormNew = document.getElementById('dev-login-form-new');
if (devLoginFormNew) {
    devLoginFormNew.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('dev-login-email').value.trim();
        const password = document.getElementById('dev-login-password').value.trim();
        const errorEl = document.getElementById('dev-login-error');
        errorEl.innerText = '';
        
        try {
            const res = await fetch('/api/auth/dev-login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Error de login');
            
            if (data.master_key) {
                masterKey = data.master_key;
                localStorage.setItem('conny_master_key', masterKey);
                localStorage.setItem('conny_dev_mode', 'true');
                devLoginModal.style.display = 'none';
                showDevBadge();
                showScreen('dashboard');
            }
        } catch(err) {
            errorEl.innerText = err.message;
        }
    });
}

const devRegForm = document.getElementById('dev-register-form');
if (devRegForm) {
    devRegForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('dev-reg-email').value.trim();
        const password = document.getElementById('dev-reg-password').value.trim();
        const devToken = document.getElementById('dev-reg-token').value.trim();
        const errorEl = document.getElementById('dev-reg-error');
        errorEl.innerText = '';
        
        try {
            const res = await fetch('/api/auth/dev-register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, dev_token: devToken })
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Error al registrar');
            
            // Switch back to login tab
            errorEl.style.color = '#34d399';
            errorEl.innerText = 'Cuenta creada. Inicia sesión.';
            setTimeout(() => {
                errorEl.innerText = '';
                errorEl.style.color = '#ef4444';
                tabDevLogin.click();
            }, 2000);
        } catch(err) {
            errorEl.style.color = '#ef4444';
            errorEl.innerText = err.message;
        }
    });
}

"""

js += "\n" + modal_js

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
