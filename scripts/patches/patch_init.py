with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

func = """
const adminChatFormElem = document.getElementById('admin-chat-form');
function initAdminChat() {
    if(adminChatInputElem && adminChatInputElem.value.trim() && adminChatFormElem) {
        adminChatFormElem.classList.add('active-input');
    } else if(adminChatFormElem) {
        adminChatFormElem.classList.remove('active-input');
    }
}
"""
with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(func + "\n" + js)
