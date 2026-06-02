import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Replace padding cell styles to be slightly distinct
js = re.sub(
    r"cell\.style\.background = 'var\(--bg-main\)';\s*cell\.style\.minHeight = '120px';",
    "cell.style.background = 'var(--bg-panel)';\n        cell.style.minHeight = '100px';",
    js
)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
