import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Heatmap gaps
content = content.replace('className="flex justify-between gap-1"', 'className="flex justify-between gap-[1px]"')
content = content.replace('className="flex flex-col gap-1"', 'className="flex flex-col gap-[1px]"')
content = content.replace('className={`w-[36px] h-[36px] rounded-md ${getHeatmapColor(dIndex, hIndex)}`}', 'className={`w-[36px] h-[36px] rounded-sm ${getHeatmapColor(dIndex, hIndex)}`}')

# 2. Search
# We need to find the exact search block and replace it
# First add import
if 'ExpandingSearchDock' not in content:
    content = content.replace('import { Sidebar } from "@/components/ui/modern-side-bar";', 'import { Sidebar } from "@/components/ui/modern-side-bar";\nimport { ExpandingSearchDock } from "@/components/ui/expanding-search-dock-shadcnui";')

search_pattern = r'\{\/\*\s*Search\s*\*\/\}\s*<div className="relative flex-1 md:w-64">.*?<\/div>'
replacement = r"""{/* Search */}
              <div className="flex-1 md:w-64 flex justify-start">
                <ExpandingSearchDock placeholder="Search..." />
              </div>"""

content = re.sub(search_pattern, replacement, content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)

