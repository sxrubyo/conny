with open('/home/ubuntu/bublee-dev-react/src/app/layout.tsx', 'r') as f:
    content = f.read()

content = content.replace(
    'import "./globals.css";',
    'import "./globals.css";\nimport { AuthProvider } from "@/components/AuthProvider";'
)

content = content.replace(
    '<body className={inter.className}>{children}</body>',
    '<body className={inter.className}><AuthProvider>{children}</AuthProvider></body>'
)

with open('/home/ubuntu/bublee-dev-react/src/app/layout.tsx', 'w') as f:
    f.write(content)
