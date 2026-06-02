import re

with open("README.md", "r") as f:
    content = f.read()

new_install = """### Step 1 — Install Conny

**Opción A: Instalación Mega Pro (GitHub + Dependencias Visuales Automáticas)**
El script oficial instalará Conny y habilitará el renderizado True-Color (Chafa) para la TUI:
```bash
curl -fsSL https://raw.githubusercontent.com/sxrubyo/conny/main/install.sh | bash
```

**Opción B: Instalación Estándar (Vía NPM)**
```bash
npm install -g conny-ai
```"""

content = re.sub(r'### Step 1 — Install Conny\n\n```bash\nnpm install -g conny-ai\n```', new_install, content)
content = content.replace("npm install -g conny-ai          # Install globally", "curl -fsSL https://raw.githubusercontent.com/sxrubyo/conny/main/install.sh | bash")

with open("README.md", "w") as f:
    f.write(content)
