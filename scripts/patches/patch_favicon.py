import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# Inject the favicon link into the head
favicon_html = '    <link rel="icon" type="image/png" href="/brand-assets/Logo_Bublee_Petalo_Claro.png">\n</head>'
content = content.replace('</head>', favicon_html)

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(content)

