import re
with open('/etc/caddy/Caddyfile', 'r') as f:
    caddyfile = f.read()

new_handle = """    handle /brand-assets/* {
        uri strip_prefix /brand-assets
        root * /home/ubuntu/bublee/brand-assets
        file_server
    }
"""
# Insert before reverse_proxy 127.0.0.1:8003
caddyfile = caddyfile.replace("    handle {\n        reverse_proxy 127.0.0.1:8003\n    }", new_handle + "\n    handle {\n        reverse_proxy 127.0.0.1:8003\n    }")

with open('/etc/caddy/Caddyfile', 'w') as f:
    f.write(caddyfile)
