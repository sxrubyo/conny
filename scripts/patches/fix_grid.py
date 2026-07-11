import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

content = content.replace(
    'gridTemplateRows: "auto 1fr"',
    'gridTemplateRows: "1fr"'
)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)

