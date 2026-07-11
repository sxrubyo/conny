import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace("import React, { useState, useEffect } from 'react';", "import React, { useState, useEffect } from 'react';\nimport { usePathname } from 'next/navigation';")

new_effect = """  const pathname = usePathname();

  useEffect(() => {
    if (pathname?.includes("/panel/instances")) {
        setActiveItem("instances");
    } else if (pathname?.includes("/analytics")) {
        setActiveItem("analytics");
    } else if (pathname?.includes("/documents")) {
        setActiveItem("documents");
    } else if (pathname?.includes("/settings")) {
        setActiveItem("settings");
    } else if (pathname?.includes("/help")) {
        setActiveItem("help");
    } else {
        setActiveItem("dashboard");
    }
"""

content = re.sub(r'  useEffect\(\(\) => \{\n    // Set active item based on current pathname\n    const path = window\.location\.pathname;\n    if \(path\.includes\("/panel/instances"\)\) \{[\s\S]*?\} else \{\n        setActiveItem\("dashboard"\);\n    \}', new_effect, content)

with open(filename, 'w') as f:
    f.write(content)
