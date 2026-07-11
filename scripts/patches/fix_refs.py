with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

prefix = """
var adminChatInputElem = document.getElementById('admin-chat-input');
var adminChatFormElem = document.getElementById('admin-chat-form');
function initAdminChat() {
    if(adminChatInputElem && adminChatInputElem.value.trim() && adminChatFormElem) {
        adminChatFormElem.classList.add('active-input');
    } else if(adminChatFormElem) {
        adminChatFormElem.classList.remove('active-input');
    }
}
var btnSwitchToDev = document.getElementById('btn-switch-to-dev');
var btnBackToAdmin = document.getElementById('btn-back-to-admin');
var tabDevLogin = document.getElementById('tab-dev-login');
var tabDevRegister = document.getElementById('tab-dev-register');
var devLoginFormNew = document.getElementById('dev-login-form-new');
"""

js = prefix + "\n" + js

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
