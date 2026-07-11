import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('href: "/analytics"', 'href: "/panel/analytics/"')
content = content.replace('href: "/documents"', 'href: "/panel/documents/"')
content = content.replace('pathname?.includes("/analytics")', 'pathname?.includes("/panel/analytics")')
content = content.replace('pathname?.includes("/documents")', 'pathname?.includes("/panel/documents")')

with open(filename, 'w') as f:
    f.write(content)
