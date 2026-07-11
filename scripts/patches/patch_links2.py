import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'r') as f:
    content = f.read()

content = content.replace("url: \"/panel\"", "url: \"/panel/\"")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'w') as f:
    f.write(content)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

content = content.replace("href: \"/panel\"", "href: \"/panel/\"")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)

with open('/home/ubuntu/bublee-dev-react/src/components/AuthProvider.tsx', 'r') as f:
    content = f.read()

content = content.replace('pathname === "/login"', 'pathname === "/login" || pathname === "/login/"')
content = content.replace('href = "/dev-portal/login"', 'href = "/dev-portal/login/"')

with open('/home/ubuntu/bublee-dev-react/src/components/AuthProvider.tsx', 'w') as f:
    f.write(content)

