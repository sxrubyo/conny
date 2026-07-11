import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# We need to find all const declarations of DOM elements that are currently at the bottom and move them up
# Let's just find everything matching `const [a-zA-Z0-9_]+ = document.getElementById(...)`
matches = re.findall(r"const ([a-zA-Z0-9_]+) = document\.getElementById\([^)]+\);", js)
for var_name in matches:
    # remove the declaration everywhere
    js = re.sub(fr"const {var_name} = document\.getElementById\((.*?)\);", "", js)

# And then put them all at the top!
all_declarations = "\n".join([f"const {var_name} = document.getElementById('{var_name.replace('Elem', '').replace('Btn', '-btn')}'); // approximation, we will extract exact strings" for var_name in matches])
# Actually, the regex above loses the exact ID! Let's do it right.

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

matches = re.findall(r"(const [a-zA-Z0-9_]+ = document\.getElementById\([^)]+\);)", js)
unique_declarations = list(set(matches))

for decl in unique_declarations:
    js = js.replace(decl, "")

# Some might be querySelectorAll
qmatches = re.findall(r"(const [a-zA-Z0-9_]+ = document\.querySelectorAll\([^)]+\);)", js)
for decl in list(set(qmatches)):
    js = js.replace(decl, "")

top_block = "\n".join(unique_declarations + list(set(qmatches)))

js = js.replace("// State Management", top_block + "\n// State Management")

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.write(js)
