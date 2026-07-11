import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# I will rewrite the countrySales part to use state and fetch.
# First, remove the hardcoded countrySales:
content = re.sub(r'const countrySales = \[.*?\];', '', content, flags=re.DOTALL)

# Add countrySales state and fetch logic
# Wait, I'll just rewrite the whole page.tsx since it's cleaner.
