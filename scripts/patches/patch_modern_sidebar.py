with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

content = content.replace("onClick: () => handleItemClick('logout')", "onClick: () => { window.location.href = '/api/auth/login'; }")
content = content.replace("onClick={() => handleItemClick('logout')}", "onClick={() => { window.location.href = '/api/auth/login'; }}")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
