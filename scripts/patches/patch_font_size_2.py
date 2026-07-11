import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

content = content.replace("font-size: clamp(40px, 6vw, 80px);", "font-size: clamp(48px, 7vw, 96px);")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

