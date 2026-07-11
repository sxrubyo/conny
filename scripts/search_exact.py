import os
import re

search_string = re.compile(r"c[oó]mo\s+se\s+llama\s+tu\s+negocio\s+para\s+mostrarte\s+c[oó]mo\s+funciono", re.IGNORECASE | re.DOTALL)

for root, dirs, files in os.walk('/home/ubuntu/bublee'):
    for f in files:
        if f.endswith('.py') or f.endswith('.txt') or f.endswith('.md') or f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if search_string.search(content):
                        print(f"MATCH FOUND IN: {path}")
            except Exception:
                pass
