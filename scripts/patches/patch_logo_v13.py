with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

import re

# Add CSS for logo-mark if it doesn't exist
css_insertion = """        .nav-logo {
            display: flex;
            align-items: center;
            font-family: var(--font-head);
            font-weight: 800;
            font-size: 22px;
            letter-spacing: -0.02em;
            color: white;
            text-decoration: none;
            gap: 12px;
        }

        .logo-mark {
            height: 48px;
            object-fit: contain;
            filter: invert(1) grayscale(100%) brightness(120%);
        }"""

content = re.sub(r'\.nav-logo \{.*?\}', css_insertion, content, flags=re.DOTALL)

# Remove the violet-dot CSS just to be clean, or leave it. We'll just replace the HTML.
old_html = """        <a href="#" class="nav-logo">
            <span class="violet-dot"></span> Bublee
        </a>"""
new_html = """        <a href="#" class="nav-logo">
            <img src="/isotype" alt="Bublee" class="logo-mark" onerror="this.style.display='none'">
        </a>"""

content = content.replace(old_html, new_html)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

