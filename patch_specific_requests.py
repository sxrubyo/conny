import re

# Read files
with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()


# === INDEX.HTML CHANGES ===
# 1. Library Add Button
html = re.sub(
    r'<div id="library-add-btn" style="aspect-ratio: 1 / 1; background: var\(--bg-main\); border: 2px dashed var\(--border-color\); border-radius: 16px;',
    r'<div id="library-add-btn" style="aspect-ratio: 1 / 1; background: var(--bg-panel); border: 1px dashed var(--border-color); border-radius: 8px;',
    html
)

# 2. Calendar Grid Container
html = re.sub(
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat\(7, 1fr\); min-width: 800px; border: 1px solid var\(--border-color\); border-radius: 12px; overflow: hidden; background: var\(--border-color\); gap: 1px;">',
    r'<div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px; gap: 8px; padding-bottom: 20px;">',
    html
)

html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=14"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)


# === APP.JS CHANGES ===
# Library Cards
js = js.replace("card.style.borderRadius = '16px';", "card.style.borderRadius = '8px';")
js = js.replace("border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;", "border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")

# Calendar Headers
js = js.replace(
    "th.style.padding = '12px';\n        th.style.borderBottom = '1px solid var(--border-color)';\n        th.style.borderRight = '1px solid var(--border-color)';",
    "th.style.padding = '8px';\n        th.style.borderBottom = '1px solid var(--border-color)';"
)

# Calendar Cells (Padding)
js = js.replace(
    "cell.style.background = 'var(--bg-main)';\n        cell.style.minHeight = '120px';\n        cell.style.borderRight = '1px solid var(--border-color)';\n        cell.style.borderBottom = '1px solid var(--border-color)';",
    "cell.style.background = 'transparent';\n        cell.style.minHeight = '120px';"
)

# Calendar Cells (Days)
old_cell_style = """        cell.style.background = 'var(--bg-main)';
        
        
        cell.style.minHeight = '120px';
        cell.style.padding = '10px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';
        
        cell.addEventListener('mouseover', () => { cell.style.background = 'var(--bg-panel)'; });
        cell.addEventListener('mouseout', () => { cell.style.background = 'var(--bg-main)'; });"""

new_cell_style = """        cell.style.background = 'var(--bg-panel)';
        cell.style.border = '1px solid var(--border-color)';
        cell.style.borderRadius = '6px';
        cell.style.minHeight = '120px';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';
        cell.style.transition = 'box-shadow 0.2s';
        
        cell.addEventListener('mouseover', () => { cell.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'; });
        cell.addEventListener('mouseout', () => { cell.style.boxShadow = 'none'; });"""

js = js.replace(old_cell_style, new_cell_style)
# Wait, my replace string might be slightly off due to empty lines left from previous replacements. Let's use regex.

js = re.sub(
    r"cell\.style\.background = 'var\(--bg-main\)';\s*cell\.style\.minHeight = '120px';\s*cell\.style\.padding = '10px';\s*cell\.style\.display = 'flex';\s*cell\.style\.flexDirection = 'column';\s*cell\.style\.gap = '4px';\s*cell\.style\.cursor = 'pointer';\s*cell\.addEventListener\('mouseover', \(\) => \{ cell\.style\.background = 'var\(--bg-panel\)'; \}\);\s*cell\.addEventListener\('mouseout', \(\) => \{ cell\.style\.background = 'var\(--bg-main\)'; \}\);",
    new_cell_style,
    js
)

# Events as Pills
old_apt_style = r"aptEl\.style\.background = apt\.status === 'confirmada' \? 'rgba\(16, 185, 129, 0\.1\)' : 'rgba\(139,92,246,0\.1\)';\s*aptEl\.style\.borderLeft = `3px solid \$\{apt\.status === 'confirmada' \? '#10b981' : 'var\(--accent-color\)'\}`;\s*aptEl\.style\.padding = '4px 8px';\s*aptEl\.style\.borderRadius = '0 4px 4px 0';\s*aptEl\.style\.fontSize = '11px';\s*aptEl\.style\.whiteSpace = 'nowrap';\s*aptEl\.style\.overflow = 'hidden';\s*aptEl\.style\.textOverflow = 'ellipsis';\s*aptEl\.style\.color = 'var\(--text-primary\)';"

new_apt_style = r"""aptEl.style.background = apt.status === 'confirmada' ? 'var(--success-color)' : 'var(--accent-color)';
            aptEl.style.color = '#ffffff';
            aptEl.style.padding = '4px 8px';
            aptEl.style.borderRadius = '6px';
            aptEl.style.fontSize = '11px';
            aptEl.style.whiteSpace = 'nowrap';
            aptEl.style.overflow = 'hidden';
            aptEl.style.textOverflow = 'ellipsis';
            aptEl.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';"""

js = re.sub(old_apt_style, new_apt_style, js)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
