import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('<div className="h-10"></div>', '')
content = content.replace('<div className="mt-8">', '<div className="mt-4">')

with open(filename, 'w') as f:
    f.write(content)
