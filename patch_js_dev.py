import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Let's fix the showScreen logic to show correct sidebar
sidebar_logic = """
function showScreen(screen) {
    loginLayout.classList.remove('active');
    dashboardLayout.classList.remove('active');

    if (screen === 'login') {
        history.pushState({}, '', '/login');
        loginLayout.classList.add('active');
    } else if (screen === 'dashboard') {
        history.pushState({}, '', '/chats');
        dashboardLayout.classList.add('active');
        
        const isDev = localStorage.getItem('conny_dev_mode') === 'true';
        const clientNav = document.getElementById('client-sidebar-nav');
        const devNav = document.getElementById('dev-sidebar-nav');
        
        if (isDev) {
            if(clientNav) clientNav.style.display = 'none';
            if(devNav) devNav.style.display = 'flex';
            // Force active tab to dev-instances
            tabViews.forEach(v => v.classList.remove('active'));
            const devInstView = document.getElementById('view-dev-instances');
            if(devInstView) devInstView.classList.add('active');
            activeTab = 'dev-instances';
            
            // Trigger load data
            loadDevInstances();
            loadDevTokens();
        } else {
            if(clientNav) clientNav.style.display = 'flex';
            if(devNav) devNav.style.display = 'none';
        }
    }
}
"""

js = re.sub(r'function showScreen\(screen\) \{.*?\}\s*\}', sidebar_logic, js, flags=re.DOTALL)

# Let's add tokens logic
tokens_logic = """
async function loadDevTokens() {
    try {
        const res = await fetch('/api/tokens', { headers: { 'X-Master-Key': masterKey } });
        if (res.ok) {
            const data = await res.json();
            const tbody = document.getElementById('dev-tokens-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';
            
            if (!data.tokens || data.tokens.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="padding:16px;text-align:center;">No hay tokens.</td></tr>';
                return;
            }
            
            data.tokens.forEach(t => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="padding:12px 16px;font-family:monospace;color:#f3f4f6;">${t.token}</td>
                    <td style="padding:12px 16px;color:#f3f4f6;">${t.clinic_label || '-'}</td>
                    <td style="padding:12px 16px;">${t.is_active ? '<span style="color:#34d399">Activo</span>' : '<span style="color:#ef4444">Usado/Inactivo</span>'}</td>
                    <td style="padding:12px 16px;text-align:right;">
                        <button class="btn" onclick="deleteToken('${t.token}')" style="background:rgba(239,68,68,0.2);color:#ef4444;border-radius:6px;padding:4px 8px;">Revocar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch(err) { console.error(err); }
}

async function deleteToken(token) {
    if(!confirm('¿Seguro que deseas revocar este token?')) return;
    try {
        await fetch(`/api/tokens/${token}`, { method: 'DELETE', headers: { 'X-Master-Key': masterKey } });
        loadDevTokens();
    } catch(err) { console.error(err); }
}

const btnCreateToken = document.getElementById('btn-dev-create-token');
if(btnCreateToken) {
    btnCreateToken.addEventListener('click', async () => {
        const label = prompt("Ingresa un nombre o etiqueta para la clínica:");
        if (!label) return;
        try {
            const res = await fetch('/api/tokens/create', { 
                method: 'POST', 
                headers: { 'X-Master-Key': masterKey, 'Content-Type': 'application/json' },
                body: JSON.stringify({ clinic_label: label })
            });
            if (res.ok) loadDevTokens();
        } catch(err) { console.error(err); }
    });
}
"""

js += "\n" + tokens_logic

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
