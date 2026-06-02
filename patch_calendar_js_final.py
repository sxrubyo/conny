import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Fix the calendar header cells styling in JS
js = js.replace(
    "th.style.padding = '4px 12px 12px 12px';",
    "th.style.padding = '12px';\n        th.style.borderBottom = '1px solid var(--border)';\n        th.style.borderRight = '1px solid var(--border)';"
)

# Fix empty padding cells
js = js.replace(
    "cell.style.background = 'transparent';\n        cell.style.minHeight = '120px';",
    "cell.style.background = 'var(--bg)';\n        cell.style.minHeight = '120px';\n        cell.style.borderRight = '1px solid var(--border)';\n        cell.style.borderBottom = '1px solid var(--border)';"
)

# Fix actual day cells
old_cell_style = """        cell.style.background = 'var(--surface)';
        cell.style.border = '1px solid var(--border)';
        cell.style.borderRadius = '12px';
        cell.style.minHeight = '120px';
        cell.style.padding = '10px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '6px';
        cell.style.cursor = 'pointer';
        cell.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)';"""

new_cell_style = """        cell.style.background = 'var(--bg)';
        cell.style.borderRight = '1px solid var(--border)';
        cell.style.borderBottom = '1px solid var(--border)';
        cell.style.minHeight = '120px';
        cell.style.padding = '10px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';
        
        cell.addEventListener('mouseover', () => { cell.style.background = 'var(--surface)'; });
        cell.addEventListener('mouseout', () => { cell.style.background = 'var(--bg)'; });"""

js = js.replace(old_cell_style, new_cell_style)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
