import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'r') as f:
    content = f.read()

content = content.replace("window.location.href = item.url;", "window.location.href = `/dev-portal${item.url}`;")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/app-sidebar.tsx', 'w') as f:
    f.write(content)


with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

content = content.replace("window.location.href = href;", "window.location.href = href.startsWith('/') && !href.startsWith('/dev-portal') ? `/dev-portal${href}` : href;")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
