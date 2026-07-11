with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

func = """
function initAdminChat() {
    if(adminChatInputElem && adminChatInputElem.value.trim() && adminChatFormElem) {
        adminChatFormElem.classList.add('active-input');
    } else if(adminChatFormElem) {
        adminChatFormElem.classList.remove('active-input');
    }
}
"""

js = js.replace("const adminChatInputElem = document.getElementById('admin-chat-input');", func + "\nconst adminChatInputElem = document.getElementById('admin-chat-input');")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
