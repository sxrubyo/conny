import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# 1. Remove glowing purple shadows from buttons
html = re.sub(r'box-shadow: 0 4px 12px rgba\(139,92,246,0\.3\);?', '', html)

# 2. Fix the Calendar Header
new_calendar_header = """
                    <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                        
                        <!-- Today Badge (Left) -->
                        <div style="background: var(--bg); color: var(--text); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border); font-weight: 600; font-size: 13px;">
                            Hoy tienes <span id="calendar-today-count" style="color: var(--primary); font-size: 14px;">0</span> citas
                        </div>
                        
                        <!-- Month Nav (Center-ish / Right aligned naturally) -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <button id="calendar-prev-btn" title="Mes Anterior" style="background: var(--bg); border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&lt;</button>
                            <h3 id="calendar-month-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text); min-width: 140px; text-align: center; text-transform: capitalize;">Mayo 2026</h3>
                            <button id="calendar-next-btn" title="Mes Siguiente" style="background: var(--bg); border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&gt;</button>
                        </div>
                    </div>
"""
# Replace the calendar header
html = re.sub(r'<div class="calendar-header".*?</div>\s*</div>', new_calendar_header, html, flags=re.DOTALL)

# 3. Fix the Calendar Grid wrapper
html = re.sub(
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat\(7, 1fr\); gap: 12px; min-width: 800px; padding-bottom: 20px;">',
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--bg);">',
    html
)

# 4. Fix Modal Background Transparencies
# Replace var(--surface) with var(--bg) for all modal main containers
# Calendar Day Modal
html = re.sub(
    r'<div style="background: var\(--surface\); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 40px rgba\(0,0,0,0\.3\); overflow: hidden; display: flex; flex-direction: column;">',
    r'<div style="background: var(--bg); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; display: flex; flex-direction: column;">',
    html
)
# Make its internal content background transparent or var(--bg) to avoid nesting issues
html = re.sub(
    r'<div id="calendar-day-modal-content" style="padding: 24px; max-height: 60vh; overflow-y: auto; background: var\(--surface\);">',
    r'<div id="calendar-day-modal-content" style="padding: 24px; max-height: 60vh; overflow-y: auto; background: var(--bg);">',
    html
)

# Library Config Modal
html = re.sub(
    r'<div style="background: var\(--surface\); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba\(0,0,0,0\.3\); overflow: hidden;">',
    r'<div style="background: var(--bg); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden;">',
    html
)

# Library Detail Modal
html = re.sub(
    r'<div style="background: var\(--surface\); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba\(0,0,0,0\.3\); overflow: hidden;">',
    r'<div style="background: var(--bg); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden;">',
    html
)

# Bump version to 12
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=12"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
