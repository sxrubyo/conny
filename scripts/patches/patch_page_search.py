import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Add import for ExpandingSearchDock
content = content.replace('import { Caveat } from \'next/font/google\';', 'import { Caveat } from \'next/font/google\';\nimport { ExpandingSearchDock } from "@/components/ui/expanding-search-dock-shadcnui";')

# Inject ExpandingSearchDock before Theme Toggle
old_topbar = """            <div className="flex items-center gap-3">
              <button 
                onClick={toggleTheme}"""

new_topbar = """            <div className="flex items-center gap-3">
              {/* Expanding Search */}
              <div className="hidden sm:block">
                <ExpandingSearchDock placeholder="Search performance..." />
              </div>

              <button 
                onClick={toggleTheme}"""

content = content.replace(old_topbar, new_topbar)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
