import re

with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    html = f.read()

# 1. Remove 'reveal' class from all elements
html = re.sub(r'\s*reveal\s*', ' ', html)

# 2. Remove the CSS for .reveal
css_reveal = r'\. \s*\{[\s\S]*?opacity:\s*0;[\s\S]*?\}'
# Actually, I'll just use a precise replace or regex
html = re.sub(r'\. \s*\{[^\}]*?opacity:\s*0[^\}]*?transform:[^\}]*?\}', '', html)
# Let's just do text replace for the specific block:
reveal_css = """        /* Animations & Reveal */
        .  {
            opacity: 0;
            transform: translateY(40px);
            transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        . .active {
            opacity: 1;
            transform: translateY(0);
        }"""
# In the previous step I removed 'reveal' from the class string. Let's just use regex to remove any class definition that has opacity 0 and translateY 40px
html = re.sub(r'\.[a-zA-Z0-9_-]+\s*\{\s*opacity:\s*0;\s*transform:\s*translateY\(40px\);\s*transition:[^\}]+\}', '', html)
html = re.sub(r'\.[a-zA-Z0-9_-]+\.active\s*\{\s*opacity:\s*1;\s*transform:\s*translateY\(0\);\s*\}', '', html)

# Wait, my previous regex `\s*reveal\s*` -> `' '` removed the string "reveal" everywhere.
# That includes the CSS definition! So the CSS became `. { ... }`.
# Let's write a safer script.
