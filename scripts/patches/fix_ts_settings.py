import re

filename = '/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('setProfile(prev => ({ ...prev, avatar: data.url }));', 'setProfile((prev: any) => ({ ...prev, avatar: data.url }));')

with open(filename, 'w') as f:
    f.write(content)
