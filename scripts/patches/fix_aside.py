import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

content = content.replace('        {children}\n      </div>\n    </>\n  );\n}', '        {children}\n      </div>\n    </aside>\n    </>\n  );\n}')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
