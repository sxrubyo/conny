import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

js = js.replace("    modal.style.display = 'flex';\n}\n}", "    modal.style.display = 'flex';\n}")

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
