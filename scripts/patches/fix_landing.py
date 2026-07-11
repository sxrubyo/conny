import os

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# 1. FIX THEME TOGGLE (document.body -> document.documentElement)
content = content.replace("document.body.classList.remove('light-theme');", "document.documentElement.classList.remove('light-theme');")
content = content.replace("document.body.classList.add('dark-theme');", "document.documentElement.classList.add('dark-theme');")
content = content.replace("document.body.classList.remove('dark-theme');", "document.documentElement.classList.remove('dark-theme');")
content = content.replace("document.body.classList.add('light-theme');", "document.documentElement.classList.add('light-theme');")
content = content.replace("document.body.classList.contains('dark-theme');", "document.documentElement.classList.contains('dark-theme');")

# Remove body class="dark-theme" since it should be on html
content = content.replace('<body class="dark-theme">', '<body>')

# 2. FIX TRANSPARENCY (lower the overlay opacity)
content = content.replace("--video-overlay: rgba(5, 5, 10, 0.82);", "--video-overlay: rgba(5, 5, 10, 0.4);")
content = content.replace("--video-overlay: rgba(250, 250, 252, 0.88);", "--video-overlay: rgba(250, 250, 252, 0.5);")

# Update glassmorphism panels to be slightly more opaque to ensure readability 
# since the background overlay is now more transparent.
content = content.replace("--bg-surface: rgba(17, 17, 24, 0.6);", "--bg-surface: rgba(17, 17, 24, 0.7);")
content = content.replace("--bg-surface: rgba(255, 255, 255, 0.7);", "--bg-surface: rgba(255, 255, 255, 0.85);")

# 3. CHANGE THE HERO TITLE
old_title = """<h1>
                Turn WhatsApp Into Your Agency's Recurring Revenue <span class="text-gradient">Machine</span>
            </h1>"""
new_title = """<h1>
                <span class="text-gradient">La Nueva Era De Agentes</span>
            </h1>"""
content = content.replace(old_title, new_title)

# Update subhead if they want Spanish context? They said "usamos español como lengua materna, adoptamos, y simplemente ponemos 'La Nueva Era De Agentes'".
old_subhead = """<p class="subhead">Deploy unlimited AI receptionists for your clients. One core. One command. Infinite instances. 85–95% margin.</p>"""
new_subhead = """<p class="subhead">Despliega agentes de IA ilimitados para tus clientes. Un solo núcleo. Un comando. Instancias infinitas.</p>"""
content = content.replace(old_subhead, new_subhead)

# 4. APPLE TYPOGRAPHY
apple_font = "font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"
content = content.replace("--font-head: 'Plus Jakarta Sans', sans-serif;", f"--font-head: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;")
content = content.replace("--font-body: 'Inter', sans-serif;", f"--font-body: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
