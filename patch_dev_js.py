with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Remove Developer Tabs Switching
import re
tabs_logic = r'// Developer Tabs Switching.*?\}\);'
js = re.sub(tabs_logic, "", js, flags=re.DOTALL)

with open("src/interfaces/web/static/app.js", "w") as f:
    js = f.write(js)
