import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Replace img with ArrowLeft
content = content.replace('<img src="/dev-portal/isotype.png" alt="Bublee Logo" className="w-6 h-6 object-contain dark:invert opacity-70 group-hover:opacity-100 transition-opacity" />', '<ArrowLeft className="w-6 h-6 text-neutral-500 dark:text-[#888] group-hover:text-[#e05a2b] transition-colors" />')

# Ensure ArrowLeft is imported
if 'ArrowLeft' not in content:
    content = content.replace('import { AreaChart,', 'import { ArrowLeft } from "lucide-react";\nimport { AreaChart,')

with open(filename, 'w') as f:
    f.write(content)
