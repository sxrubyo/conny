import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

js = js.replace("loginLayout.classList", "loginScreen.classList")

declarations = """
// --- Added missing dev view elements at top ---
const navItems = document.querySelectorAll('.nav-item');
const chatSearch = document.getElementById('chat-search');
const chatSendForm = document.getElementById('chat-send-form');
const adminChatForm = document.getElementById('admin-chat-form');
const onboardingForm = document.getElementById('onboarding-register-form') || document.getElementById('onboarding-form');

const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
const devLoginFormNew = document.getElementById('dev-login-form-new');
const devRegisterForm = document.getElementById('dev-register-form');
const tabDevRegister = document.getElementById('tab-dev-register');
const devLoginTabContent = document.getElementById('dev-login-tab-content');
const devRegisterTabContent = document.getElementById('dev-register-tab-content');
const devLoginError = document.getElementById('dev-login-error');
const devLoginEmail = document.getElementById('dev-login-email');
const devLoginPassword = document.getElementById('dev-login-password');
const devRegEmail = document.getElementById('dev-reg-email');
const devRegPassword = document.getElementById('dev-reg-password');
const devRegToken = document.getElementById('dev-reg-token');

const adminChatInputElem = document.getElementById('admin-chat-input');
const adminChatFormElem = document.getElementById('admin-chat-form');

function initAdminChat() {
    if(adminChatInputElem && adminChatInputElem.value.trim() && adminChatFormElem) {
        adminChatFormElem.classList.add('active-input');
    } else if(adminChatFormElem) {
        adminChatFormElem.classList.remove('active-input');
    }
}
// ----------------------------------------------
"""
# Strip out redeclarations at the bottom
js = re.sub(r"const devLoginFormNew = document\.getElementById\('dev-login-form-new'\);", "", js)
js = re.sub(r"const devRegForm = document\.getElementById\('dev-register-form'\);", "", js)
js = re.sub(r"const devRegisterTabContent = document\.getElementById\('dev-register-tab-content'\);", "", js)
js = re.sub(r"const devLoginTabContent = document\.getElementById\('dev-login-tab-content'\);", "", js)
js = re.sub(r"const tabDevRegister = document\.getElementById\('tab-dev-register'\);", "", js)
js = re.sub(r"const tabDevLogin = document\.getElementById\('tab-dev-login'\);", "const tabDevLogin = document.getElementById('tab-dev-login');", js) # keep one

js = js.replace("// State Management", declarations + "\n// State Management")

# Fix the naked tabDevRegister.addEventListener
js = js.replace("    tabDevRegister.addEventListener('click', () => {", "    if (tabDevRegister) tabDevRegister.addEventListener('click', () => {")

# Fix the naked adminChatInputElem.addEventListener
js = js.replace("    adminChatInputElem.addEventListener('blur', () => {", "    if (adminChatInputElem) adminChatInputElem.addEventListener('blur', () => {")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
