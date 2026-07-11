import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Add position: "relative" to style
content = content.replace(
    'style={{ gridRow: "1 / -1", height: "100vh", overflowY: "auto" }}',
    'style={{ gridRow: "1 / -1", height: "100vh", overflowY: "auto", position: "relative" }}'
)

# Render children at the end
content = content.replace(
    '        </div>\n      </div>\n      </>\n  );\n}',
    '        </div>\n        {children}\n      </div>\n      </>\n  );\n}'
)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
