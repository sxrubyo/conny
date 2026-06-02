import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Make cells white (or dark bg-main in dark mode) against the gray bg-panel-hover container
js = js.replace("cell.style.background = 'var(--bg-panel)';", "cell.style.background = 'var(--bg-main)';")

# We had hover effects setting it to bg-panel
js = re.sub(
    r"cell\.addEventListener\('mouseover', \(\) => \{ cell\.style\.boxShadow = '0 4px 12px rgba\(0,0,0,0\.08\)'; \}\);\s*cell\.addEventListener\('mouseout', \(\) => \{ cell\.style\.boxShadow = 'none'; \}\);",
    "cell.addEventListener('mouseover', () => { cell.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'; cell.style.borderColor = 'var(--accent-color)'; });\n        cell.addEventListener('mouseout', () => { cell.style.boxShadow = 'none'; cell.style.borderColor = 'var(--border-color)'; });",
    js
)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
