import os

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Remove the BUBLEE text
old_logo_html = """<a href="#" class="logo">
                <img src="/isotype" alt="Bublee" class="logo-mark" onerror="this.style.display='none'">
                BUBLEE
            </a>"""
new_logo_html = """<a href="#" class="logo">
                <img src="/isotype" alt="Bublee" class="logo-mark" onerror="this.style.display='none'">
            </a>"""
content = content.replace(old_logo_html, new_logo_html)

# Increase logo size
content = content.replace("""        .logo-mark {
            height: 32px;""", """        .logo-mark {
            height: 48px;""")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
