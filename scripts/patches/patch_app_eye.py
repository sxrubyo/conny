with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

eye_script = """
// --- Password Toggle Logic ---
const togglePasswordBtn = document.getElementById('toggle-password');
const loginPasswordInput = document.getElementById('login-password');
if (togglePasswordBtn && loginPasswordInput) {
    togglePasswordBtn.addEventListener('click', () => {
        const type = loginPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        loginPasswordInput.setAttribute('type', type);
        
        // Use Lucide icons to swap eye/eye-off
        const iconName = type === 'password' ? 'eye' : 'eye-off';
        togglePasswordBtn.innerHTML = `<i data-lucide="${iconName}" style="width: 20px; height: 20px;"></i>`;
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    });
}
"""

js = js + "\n" + eye_script

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
