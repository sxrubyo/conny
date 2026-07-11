import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/topbar.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('export function Topbar({ title, subtitle, isDark, setIsDark }: any) {', 'export function Topbar({ title, subtitle, isDark, setIsDark, children }: any) {')
content = content.replace('{/* Theme Toggle */}', '{children}\n        {/* Theme Toggle */}')

with open(filename, 'w') as f:
    f.write(content)
