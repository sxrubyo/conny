import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Completely replace the corrupted calendar-header to calendar-grid-content section
start_marker = '<div class="calendar-container"'
end_marker = '<!-- Header and cells injected by JS so alignment is perfect -->'
start_idx = html.find(start_marker)
end_idx = html.find(end_marker) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    clean_html = """<div class="calendar-container" style="flex: 1; display: flex; flex-direction: column; background: var(--bg-main); padding: 24px; overflow: hidden;">
                    <div class="calendar-header" style="display: flex; align-items: center; justify-content: center; margin-bottom: 24px; position: relative;">
                        <!-- Month Nav (Centered) -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <button id="calendar-prev-btn" title="Mes Anterior" style="background: var(--bg-main); border: 1px solid var(--border-color); color: var(--text-primary); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&lt;</button>
                            <h3 id="calendar-month-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-primary); min-width: 140px; text-align: center; text-transform: capitalize;">Mayo 2026</h3>
                            <button id="calendar-next-btn" title="Mes Siguiente" style="background: var(--bg-main); border: 1px solid var(--border-color); color: var(--text-primary); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&gt;</button>
                        </div>

                        <!-- Today Badge (Absolute Right) -->
                        <div style="position: absolute; right: 0; background: var(--bg-main); color: var(--text-primary); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border-color); font-weight: 600; font-size: 13px;">
                            Hoy tienes <span id="calendar-today-count" style="color: var(--accent-color); font-size: 14px;">0</span> citas
                        </div>
                    </div>

                    <div style="flex: 1; overflow-y: auto; background: var(--bg-panel-hover); border-radius: 12px; border: 1px solid var(--border-color); padding: 12px;">
                        <div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px; gap: 8px; padding-bottom: 20px;">
                            <!-- Header and cells injected by JS so alignment is perfect -->"""
    
    html = html[:start_idx] + clean_html + html[end_idx:]

# Bump version to v15
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=15"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
