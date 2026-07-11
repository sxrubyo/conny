import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Remove Fontshare
old_fonts = """    <!-- Premium Fonts from Fontshare -->
    <link href="https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&f[]=switzer@400,500,600&display=swap" rel="stylesheet">"""

# Replace with nothing (just system fonts) or Inter as a fallback
new_fonts = """    <!-- Apple System Fonts Stack -->"""

content = content.replace(old_fonts, new_fonts)

# Update CSS variables
old_vars = """            --font-head: 'Clash Display', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: 'Switzer', -apple-system, BlinkMacSystemFont, sans-serif;"""

new_vars = """            --font-head: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            --font-body: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;"""

content = content.replace(old_vars, new_vars)

# Fix the H1 spacing if I changed it
# Apple uses very tight letter spacing for big headings
content = content.replace("letter-spacing: -0.02em;\n            font-weight: 600;", "letter-spacing: -0.04em;\n            font-weight: 800;")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
