import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Remove toggleTheme logic and button
content = re.sub(r'  const toggleTheme.*?};\n\n', '\n', content, flags=re.DOTALL)
content = re.sub(r'            <div\n              onClick=\{toggleTheme\}.*?</div>', '', content, flags=re.DOTALL)
content = content.replace('Sun, Moon,', '')

with open(filename, 'w') as f:
    f.write(content)
