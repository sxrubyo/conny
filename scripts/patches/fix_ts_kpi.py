import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace(']).map((kpi, i) => (', ']).map((kpi: any, i: number) => (')

with open(filename, 'w') as f:
    f.write(content)
