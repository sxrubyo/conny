import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Replace: const dateString = cellDate.toISOString().split('T')[0];
# With: const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
js = js.replace(
    "const dateString = cellDate.toISOString().split('T')[0];",
    "const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;"
)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
