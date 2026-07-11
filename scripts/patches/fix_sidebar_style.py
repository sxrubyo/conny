import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

content = content.replace('style={{ gridRow: "1 / -1", height: "100vh", overflowY: "auto", position: "relative" }}', 'style={{ height: "100%", overflowY: "auto", position: "relative" }}')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
