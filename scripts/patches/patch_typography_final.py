import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Update font imports
content = content.replace(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@900&family=Playfair+Display:ital,wght@1,600&display=swap" rel="stylesheet">',
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@900&family=Playfair+Display:ital,wght@1,400&display=swap" rel="stylesheet">'
)

# 2. Update accent text CSS (weight 400)
old_accent_css = """        .text-accent-infinite {
            color: #E040FB; /* bright magenta-pink */
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-weight: 600;
            /* Remove gradient clipping so it renders solid and sharp */
            background: none;
            -webkit-background-clip: unset;
            -webkit-text-fill-color: unset;
            background-clip: unset;
            padding-right: 8px;
        }"""
new_accent_css = """        .text-accent-infinite {
            color: #E040FB; /* bright magenta-pink */
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-weight: 400; /* Delicate weight */
            background: none;
            -webkit-background-clip: unset;
            -webkit-text-fill-color: unset;
            background-clip: unset;
            padding-right: 8px;
        }"""
content = content.replace(old_accent_css, new_accent_css)

# 3. Update HTML to ensure "Un Agente." and "Clientes." are 900
old_h1_span = """<span style="font-weight: 600;">Clientes.</span>"""
new_h1_span = """Clientes."""
content = content.replace(old_h1_span, new_h1_span)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

