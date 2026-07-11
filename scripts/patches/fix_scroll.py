import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Revert html/body css
bad_css = """        html {
            scroll-snap-type: y mandatory;
            scroll-behavior: smooth;
        }
        
        body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
        }"""
good_css = """        html, body {
            background-color: var(--bg-void);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }"""
content = content.replace(bad_css, good_css)

# Remove height: 100vh and scroll snap from hero
content = content.replace("height: 100vh; /* Fixed height for snap */", "min-height: 100vh;")
content = content.replace("scroll-snap-align: start;\n            scroll-snap-stop: always;", "")

# Remove from sdk
content = content.replace("height: 100vh; display: flex; align-items: center; justify-content: center; scroll-snap-align: start; scroll-snap-stop: always;", "min-height: 100vh; display: flex; align-items: center; justify-content: center;")

# Remove from section
content = content.replace(".section {\n            scroll-snap-align: start;\n            min-height: 100vh;\n            display: flex;\n            flex-direction: column;\n            justify-content: center;", ".section {")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
