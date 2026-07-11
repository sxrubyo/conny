import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# 1. Fix loginLayout typo
js = js.replace("loginLayout.classList", "loginScreen.classList")

# 2. Add missing variables at the top
missing_vars = """
const developerLoginView = document.getElementById('developer-login-view');
const standardLoginView = document.getElementById('standard-login-view');
const navItems = document.querySelectorAll('.nav-item');
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const devRegisterForm = document.getElementById('dev-register-form');
const onboardingForm = document.getElementById('onboarding-register-form') || document.getElementById('onboarding-form');
const chatSearch = document.getElementById('chat-search');
const chatSendForm = document.getElementById('chat-send-form');
const adminChatForm = document.getElementById('admin-chat-form');
const tabDevRegister = document.getElementById('tab-dev-register');
const tabDevLogin = document.getElementById('tab-dev-login');
"""
js = js.replace("const loginScreen = document.getElementById('login-screen');", "const loginScreen = document.getElementById('login-screen');\n" + missing_vars)

# 3. Fix adminChatInputElem issue (add missing declaration)
admin_chat_fix = """
const adminChatInputElem = document.getElementById('admin-chat-input');
const adminChatFormElem = document.getElementById('admin-chat-form');
if (adminChatInputElem) {
    adminChatInputElem.addEventListener('blur', () => {
"""
js = js.replace("    adminChatInputElem.addEventListener('blur', () => {", admin_chat_fix)

# 4. Remove duplicate dev definitions that are throwing redeclaration errors or ReferenceErrors.
# Let's just remove the ones at the bottom or top.
# The `btnSwitchToDev` and `tabDevRegister` were missing because they were declared at the bottom. 
# We declared them at the top now! So the `const` at the bottom will throw an error "Identifier 'btnSwitchToDev' has already been declared".
js = js.replace("const btnSwitchToDev = document.getElementById('btn-switch-to-dev');", "")
js = js.replace("const tabDevRegister = document.getElementById('tab-dev-register');", "")
js = js.replace("const tabDevLogin = document.getElementById('tab-dev-login');", "")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
