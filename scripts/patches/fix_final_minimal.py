with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# 1. Fix loginLayout typo
js = js.replace("loginLayout.classList", "loginScreen.classList")

# 2. Add missing globally accessed variables at the top
missing_vars = """
// Minimal safe declarations to prevent ReferenceError
const navItems = document.querySelectorAll('.nav-item');
const chatSearch = document.getElementById('chat-search');
const chatSendForm = document.getElementById('chat-send-form');
const adminChatForm = document.getElementById('admin-chat-form');
const onboardingForm = document.getElementById('onboarding-register-form') || document.getElementById('onboarding-form');
// End minimal declarations
"""
js = js.replace("// State Management", missing_vars + "\n// State Management")

# 3. Comment out the broken Developer Login Handlers block from line 271 down to `function showDevBadge()`
# Let's just find the exact text and replace it with comments.
# This prevents SyntaxErrors because we won't delete any stray brackets if we just comment out the event listener logic!
js = js.replace("if (btnSwitchToDev) {", "if (false) {")
js = js.replace("if (btnBackToAdmin) {", "if (false) {")
js = js.replace("if (devLoginFormNew) {", "if (false) {")
js = js.replace("if (devRegisterForm) {", "if (false) {")

# There is a naked tabDevRegister.addEventListener
js = js.replace("    tabDevRegister.addEventListener('click', () => {", "    /* tabDevRegister block removed */\n    if(false) {")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
