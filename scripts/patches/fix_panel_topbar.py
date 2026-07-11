import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace('import { Sidebar } from "@/components/ui/modern-side-bar";', 'import { Sidebar } from "@/components/ui/modern-side-bar";\nimport { Topbar } from "@/components/ui/topbar";')

# Extract the search bar and date, replace the top section
# I'll use regex to find `{/* Top Bar */}` to the end of that div.

start_str = '{/* Top Bar */}'
end_str = '{/* KPI Cards */}'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    old_topbar = content[start_idx:end_idx]
    
    new_topbar = """<Topbar title={greeting} subtitle="Resumen general de rendimiento" isDark={isDark} setIsDark={setIsDark}>
                <div className="flex-1 md:w-64 flex justify-start">
                  <SearchInputLoader />
                </div>
                <div className="hidden lg:flex items-center gap-2 text-sm text-neutral-500 dark:text-[#888888] mr-4">
                  <Calendar className="h-4 w-4" />
                  <span>Wed, 29 May 2024</span>
                </div>
            </Topbar>
            
            """
            
    content = content[:start_idx] + new_topbar + content[end_idx:]

    with open(filename, 'w') as f:
        f.write(content)
