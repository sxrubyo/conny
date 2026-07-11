with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# We want to find:
#     } else if (screen === 'dashboard') {
#         const isDevInit = localStorage.getItem('bublee_dev_mode') === 'true';
#         if (isDevInit) {
#                 
#             window.location.href = '/dev-portal';
#             return;
#         }

import re
# Clean up the mess
js = re.sub(r"} else if \(screen === 'dashboard'\) \{[\s\S]*?history\.pushState\(\{\}, '', '/chats'\);", 
"""} else if (screen === 'dashboard') {
        const isDevInit = localStorage.getItem('bublee_dev_mode') === 'true';
        if (isDevInit) {
            window.location.href = '/dev-portal';
            return;
        }
        history.pushState({}, '', '/chats');""", js, count=1)

with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
