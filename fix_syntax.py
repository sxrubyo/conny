import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Replace the specific faulty line
js = js.replace("libModal.style.display = 'flex';\n        }\n    });", "libModal.style.display = 'flex';\n        }")
js = js.replace("libModal.style.display = 'flex';\n        }\n    ", "libModal.style.display = 'flex';\n        }\n    });\n    ")

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
