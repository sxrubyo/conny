import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Hero overall vertical space
content = content.replace("            padding-top: 80px; /* Offset for nav */", "            padding-top: 140px; /* More breathing room below nav */")

# 2. H1 text spacing
content = content.replace("line-height: 1.05;", "line-height: 1.15;")
content = content.replace("letter-spacing: -0.04em;\n            font-weight: 800;", "letter-spacing: -0.01em;\n            font-weight: 700;")
content = content.replace("margin-bottom: 32px;", "margin-bottom: 48px;")

# 3. Subline spacing
content = content.replace("margin-bottom: 48px;", "margin-bottom: 64px;")
content = content.replace("line-height: 1.6;", "line-height: 1.7;")
content = content.replace("max-width: 600px;", "max-width: 650px;")

# 4. Navbar link spacing (if they meant all text)
content = content.replace("letter-spacing: 0.05em;", "letter-spacing: 0.08em;")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

