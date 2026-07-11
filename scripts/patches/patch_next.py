with open('/home/ubuntu/bublee-dev-react/next.config.mjs', 'r') as f:
    content = f.read()

if 'trailingSlash' not in content:
    content = content.replace("basePath: '/dev-portal',", "basePath: '/dev-portal',\n  trailingSlash: true,")

with open('/home/ubuntu/bublee-dev-react/next.config.mjs', 'w') as f:
    f.write(content)
