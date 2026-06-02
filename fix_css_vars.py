import re

def fix_vars(content):
    content = content.replace('var(--bg)', 'var(--bg-main)')
    content = content.replace('var(--surface)', 'var(--bg-panel)')
    content = content.replace('var(--text)', 'var(--text-primary)')
    content = content.replace('var(--text-muted)', 'var(--text-secondary)')
    content = content.replace('var(--border)', 'var(--border-color)')
    content = content.replace('var(--primary)', 'var(--accent-color)')
    return content

# Read files
with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Fix vars
html = fix_vars(html)
js = fix_vars(js)

# Fix Calendar Grid CSS Strategy in JS
js = js.replace(
    "th.style.borderBottom = '1px solid var(--border-color)';\n        th.style.borderRight = '1px solid var(--border-color)';",
    "" # Remove borders from cells because we will use gap
)
js = js.replace(
    "cell.style.borderRight = '1px solid var(--border-color)';\n        cell.style.borderBottom = '1px solid var(--border-color)';",
    "" # Remove from padding cells
)
js = js.replace(
    "cell.style.borderRight = '1px solid var(--border-color)';\n        cell.style.borderBottom = '1px solid var(--border-color)';",
    "" # Remove from main cells
)

# Fix JS Calendar Header alignment 
html = re.sub(
    r'<div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">\s*<!-- Today Badge \(Left\) -->\s*<div style="background: var\(--bg-main\); color: var\(--text-primary\); padding: 8px 16px; border-radius: 8px; border: 1px solid var\(--border-color\); font-weight: 600; font-size: 13px;">\s*Hoy tienes <span id="calendar-today-count" style="color: var\(--accent-color\); font-size: 14px;">0</span> citas\s*</div>\s*<!-- Month Nav \(Center-ish / Right aligned naturally\) -->\s*<div style="display: flex; align-items: center; gap: 16px;">',
    """<div class="calendar-header" style="display: flex; align-items: center; margin-bottom: 24px; position: relative; justify-content: center;">
                        <!-- Month Nav (Centered) -->
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <button id="calendar-prev-btn" title="Mes Anterior" style="background: var(--bg-main); border: 1px solid var(--border-color); color: var(--text-primary); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&lt;</button>
                            <h3 id="calendar-month-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text-primary); min-width: 140px; text-align: center; text-transform: capitalize;">Mayo 2026</h3>
                            <button id="calendar-next-btn" title="Mes Siguiente" style="background: var(--bg-main); border: 1px solid var(--border-color); color: var(--text-primary); width: 36px; height: 36px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">&gt;</button>
                        </div>
                        
                        <!-- Today Badge (Absolute Right) -->
                        <div style="position: absolute; right: 0; background: var(--bg-main); color: var(--text-primary); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border-color); font-weight: 600; font-size: 13px;">
                            Hoy tienes <span id="calendar-today-count" style="color: var(--accent-color); font-size: 14px;">0</span> citas
                        </div>""",
    html, flags=re.DOTALL
)

# Fix Calendar Grid Container in HTML to use background/gap method for perfect borders
html = re.sub(
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat\(7, 1fr\); min-width: 800px; border: 1px solid var\(--border-color\); border-radius: 12px; overflow: hidden; background: var\(--bg-main\);">',
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px; border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; background: var(--border-color); gap: 1px;">',
    html
)

html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=13"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
