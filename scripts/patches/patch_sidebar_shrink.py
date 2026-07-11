import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Replace <aside className="... w-56 ..."> with shrink-0
# Let's search for '<aside' and add shrink-0
content = re.sub(r'<aside\s+className="([^"]+)"', lambda m: f'<aside className="{m.group(1)} shrink-0"' if 'shrink-0' not in m.group(1) else m.group(0), content)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
