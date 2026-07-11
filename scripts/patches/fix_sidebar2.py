import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('<div className="flex items-center space-x-3 w-full">', '<div className={`flex items-center ${isCollapsed ? "justify-center w-full" : "space-x-3 w-full"}`}>')

with open(filename, 'w') as f:
    f.write(content)
