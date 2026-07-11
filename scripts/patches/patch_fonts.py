import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Replace Google Fonts links with Fontshare links
old_fonts = """    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">"""

new_fonts = """    <!-- Premium Fonts from Fontshare -->
    <link href="https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&f[]=switzer@400,500,600&display=swap" rel="stylesheet">"""

content = content.replace(old_fonts, new_fonts)

# Update CSS variables
old_vars = """            --font-head: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;"""

new_vars = """            --font-head: 'Clash Display', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-body: 'Switzer', -apple-system, BlinkMacSystemFont, sans-serif;"""

content = content.replace(old_vars, new_vars)

# Enhance H1 style slightly for Clash Display
# It looks best with slightly tighter letter-spacing and heavier weight
content = content.replace("letter-spacing: -0.04em;", "letter-spacing: -0.02em;\n            font-weight: 600;")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
