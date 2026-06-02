import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Fix the calendar container wrapper
html = re.sub(
    r'<div style="flex: 1; overflow-y: auto; background: var\(--bg-panel-hover\); border-radius: 12px; border: 1px solid var\(--border-color\); padding: 12px;">\s*<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat\(7, 1fr\); min-width: 800px; gap: 8px; padding-bottom: 20px;">',
    r'<div style="flex: 1; overflow-y: auto;">\n                        <div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px; gap: 1px; background: var(--border-color); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden;">',
    html
)

html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=16"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
