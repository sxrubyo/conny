import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Revert and shrink H1
content = content.replace("font-size: clamp(64px, 8vw, 120px);", "font-size: clamp(40px, 6vw, 80px);")
content = content.replace("line-height: 1.15;", "line-height: 1.05;")
content = content.replace("letter-spacing: -0.01em;\n            font-weight: 700;", "letter-spacing: -0.03em;\n            font-weight: 800;")
content = content.replace("margin-bottom: 48px;", "margin-bottom: 24px;")

# Revert subline
content = content.replace("margin-bottom: 64px;", "margin-bottom: 40px;")
content = content.replace("line-height: 1.7;", "line-height: 1.6;")

# Reduce padding a bit so it's not weirdly floating
content = content.replace("padding-top: 140px; /* More breathing room below nav */", "padding-top: 100px;")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

