import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# remove the last bracket if it's the last non-whitespace character
js = js.rstrip()
if js.endswith("}"):
    js = js[:-1]

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
