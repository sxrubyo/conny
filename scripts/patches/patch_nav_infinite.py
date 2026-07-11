import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. Navbar Height & Pro Look
old_nav_css = """        nav {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 100;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            background: var(--nav-bg);
            padding: 0 4vw;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }"""

new_nav_css = """        nav {
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 100;
            backdrop-filter: blur(32px) saturate(120%);
            -webkit-backdrop-filter: blur(32px) saturate(120%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(5, 5, 10, 0.65); /* Sleek, dark glass */
            padding: 0 4vw;
            height: 100px; /* Más ancho (alto) */
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .text-accent-infinite {
            background: linear-gradient(135deg, #7C3AED 0%, #C026D3 50%, #F59E0B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }"""

content = content.replace(old_nav_css, new_nav_css)

# 2. Add text-accent to "Infinite"
old_h1 = """            <h1 class="fade-up d-2">
                One Agent.<br>
                Infinite Clients.
            </h1>"""
new_h1 = """            <h1 class="fade-up d-2">
                One Agent.<br>
                <span class="text-accent-infinite">Infinite</span> Clients.
            </h1>"""
content = content.replace(old_h1, new_h1)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)

