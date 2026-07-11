import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Replace the Middle Row gridTemplateColumns
old_grid = '<div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }} className="mb-4">'
new_grid = '<div style={{ display: "grid", gridTemplateColumns: "auto minmax(0, 1fr)", gap: 12 }} className="mb-4">'

content = content.replace(old_grid, new_grid)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
