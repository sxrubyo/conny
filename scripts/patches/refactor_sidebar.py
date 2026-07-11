import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# We need to target the main wrapper of the sidebar.
# In `modern-side-bar.tsx`:
#      <div
#        className={`
#          fixed top-0 left-0 h-full bg-neutral-50 dark:bg-[#111111] border-r border-neutral-200 dark:border-neutral-800 z-40 transition-all duration-300 flex flex-col shrink-0
#          ${isOpen ? "translate-x-0" : "-translate-x-full"}
#          ${isCollapsed ? "w-20" : "w-56"}
#          md:translate-x-0 md:static md:z-auto
#          ${className}
#        `}
#      >

wrapper_pattern = r'<div\s+className={`\s*fixed top-0 left-0 h-full bg-neutral-50 dark:bg-\[#111111\] border-r border-neutral-200 dark:border-neutral-800 z-40 transition-all duration-300 flex flex-col shrink-0\s*\$\{isOpen \? "translate-x-0" : "-translate-x-full"\}\s*\$\{isCollapsed \? "w-20" : "w-56"\}\s*md:translate-x-0 md:static md:z-auto\s*\$\{className\}\s*`}\s*>'
new_wrapper = """      <div
        className={`
          bg-neutral-50 dark:bg-[#111111] border-r border-neutral-200 dark:border-neutral-800 z-40 flex flex-col
          ${isOpen ? "fixed inset-y-0 left-0 translate-x-0" : "max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:-translate-x-full"}
          md:translate-x-0
          ${className}
        `}
        style={{ gridRow: "1 / -1", height: "100vh", overflowY: "auto" }}
      >"""

# Wait, the shrink-0 might or might not be there. Let's just use regex that allows variable whitespace and properties.
content = re.sub(r'<div\s+className={`[^`]+`}\s*>', new_wrapper, content, count=1)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)

