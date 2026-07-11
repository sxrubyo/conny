with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'r') as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if "} else if (screen === 'dashboard') {" in line:
        out.append(line)
        out.append("        const isDev = localStorage.getItem('bublee_dev_mode') === 'true';\n")
        out.append("        if (isDev) {\n")
        out.append("            window.location.href = '/dev-portal';\n")
        out.append("            return;\n")
        out.append("        }\n")
    else:
        out.append(line)

with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/app.js', 'w') as f:
    f.writelines(out)
with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'w') as f:
    f.writelines(out)
