with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Reduce font size
content = content.replace('font-size: clamp(56px, 8vw, 110px);', 'font-size: clamp(48px, 7vw, 96px);')

# 2. Add space to hero content
# We will add margin-top to .hero-content to push it down from the center
content = content.replace('.hero-content {', '.hero-content {\n            margin-top: 60px;')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

