import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Add Google Fonts link for Playfair Display Italic
font_link = """    <!-- Premium Italic Font -->
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,600&display=swap" rel="stylesheet">"""

content = content.replace("    <!-- Apple System Fonts Stack -->", "    <!-- Apple System Fonts Stack -->\n" + font_link)

# Update CSS for text-accent-infinite
old_css = """        .text-accent-infinite {
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 50%, #F59E0B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }"""

new_css = """        .text-accent-infinite {
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 50%, #F59E0B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-weight: 600;
            padding-right: 8px; /* Evita que se corte la cursiva por el clip de texto */
        }"""

content = content.replace(old_css, new_css)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

