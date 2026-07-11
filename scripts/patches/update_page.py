import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Update setSidebarWidth bounds
old_drag = 'setSidebarWidth(Math.min(360, Math.max(180, newWidth)));'
new_drag = 'setSidebarWidth(Math.min(360, Math.max(80, newWidth)));'
content = content.replace(old_drag, new_drag)

# 2. Add isCollapsed computed value
# Find const [sidebarWidth, setSidebarWidth] = useState(240);
old_state = 'const [sidebarWidth, setSidebarWidth] = useState(240);'
new_state = 'const [sidebarWidth, setSidebarWidth] = useState(240);\n  const isCollapsed = sidebarWidth < 120;'
content = content.replace(old_state, new_state)

# 3. Update Sidebar invocation
old_sidebar = '<Sidebar>'
new_sidebar = '<Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)}>'
content = content.replace(old_sidebar, new_sidebar)

# 4. Replace ExpandingSearchDock with SearchInputLoader
content = content.replace('import { ExpandingSearchDock } from "@/components/ui/expanding-search-dock-shadcnui";', 'import { SearchInputLoader } from "@/components/ui/search-input-loader";')
content = content.replace('<ExpandingSearchDock placeholder="Search..." />', '<SearchInputLoader />')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
