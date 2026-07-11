import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Add Inter 900 to the fonts
old_fonts = """    <!-- Premium Italic Font -->
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,600&display=swap" rel="stylesheet">"""
new_fonts = """    <!-- Premium Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@900&family=Playfair+Display:ital,wght@1,600&display=swap" rel="stylesheet">"""
content = content.replace(old_fonts, new_fonts)

# 2. Update H1 CSS
# Find the .hero h1 block and replace it
h1_css_old = """        .hero h1 {
            font-family: var(--font-head);
            font-size: clamp(48px, 7vw, 96px);
            line-height: 1.05;
            letter-spacing: -0.03em;
            font-weight: 800;
            margin-bottom: 24px;
            color: white;
            text-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }"""
h1_css_new = """        .hero h1 {
            font-family: 'Inter', sans-serif;
            font-size: clamp(56px, 8vw, 110px);
            line-height: 1.05;
            letter-spacing: 0;
            font-weight: 900;
            margin-bottom: 24px;
            color: white;
            text-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }"""
if h1_css_old in content:
    content = content.replace(h1_css_old, h1_css_new)
else:
    # Use regex if exact match fails
    content = re.sub(r'\.hero h1 \{[^}]+\}', h1_css_new, content)

# 3. Update the accent word "Infinite"
accent_css_old = """        .text-accent-infinite {
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 50%, #F59E0B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Playfair Display', serif;
            font-style: italic;
            font-weight: 600;
            padding-right: 8px; /* Evita que se corte la cursiva por el clip de texto */
        }"""
accent_css_new = """        .text-accent-infinite {
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
if accent_css_old in content:
    content = content.replace(accent_css_old, accent_css_new)
else:
    content = re.sub(r'\.text-accent-infinite \{[^}]+\}', accent_css_new, content)

# Just to be sure the HTML has the periods
content = content.replace("One Agent.<br>", "One Agent.<br>")
content = content.replace("</span> Clients.", "</span> Clients.")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
