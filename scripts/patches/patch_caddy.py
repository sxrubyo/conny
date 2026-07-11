with open('/etc/caddy/Caddyfile', 'r') as f:
    content = f.read()
content = content.replace("root * /home/ubuntu/bublee/brand-assets", "root * /var/www/bublee")
with open('/etc/caddy/Caddyfile', 'w') as f:
    f.write(content)
