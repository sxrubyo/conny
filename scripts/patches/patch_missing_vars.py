with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

declarations = """
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
const devRegisterForm = document.getElementById('dev-register-form');
const onboardingForm = document.getElementById('onboarding-register-form') || document.getElementById('onboarding-form');
const chatSearch = document.getElementById('chat-search');
const chatSendForm = document.getElementById('chat-send-form');
const adminChatForm = document.getElementById('admin-chat-form');
"""

js = js.replace("// Elementos de Acceso Estándar", declarations + "\n// Elementos de Acceso Estándar")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
