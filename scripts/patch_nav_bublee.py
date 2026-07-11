import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

old_logo = """        <a href="#" class="nav-logo">
            <img src="/isotype" alt="Bublee AI" class="logo-mark" onerror="this.style.display='none'">
            Bublee AI
        </a>"""

new_logo = """        <a href="#" class="nav-logo">
            <img src="/isotype" alt="Bublee" class="logo-mark" onerror="this.style.display='none'">
            Bublee
        </a>"""

content = content.replace(old_logo, new_logo)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
