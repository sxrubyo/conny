import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Reduce top padding/space
content = content.replace("padding-top: 100px;", "padding-top: 60px;")

# 2. Change the eyebrow text
content = content.replace("✦ Open Source AI Receptionist", "✦ Next-Gen AI Receptionist Platform")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

