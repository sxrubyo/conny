import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

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

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(missing_vars + "\n" + js)
