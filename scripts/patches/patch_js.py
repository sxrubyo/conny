import re
with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

force_refresh_code = """
document.addEventListener('DOMContentLoaded', () => {
    // FORCE CACHE BUST IF HTML IS OLD
    if (localStorage.getItem('bublee_dev_mode') === 'true' && !document.getElementById('view-dev-ai-chat')) {
        if (!window.location.href.includes('cachebust')) {
            window.location.href = '/app?cachebust=' + Date.now();
        }
    }
});
"""

if "FORCE CACHE BUST" not in js:
    js = force_refresh_code + js
    with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'w') as f:
        f.write(js)
    with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
        f.write(js)
