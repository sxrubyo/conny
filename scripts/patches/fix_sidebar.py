import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Fix the logo container padding when collapsed
old_header = r'className={`flex items-center justify-between p-5 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-\[#111111\]/60 \$\{isCollapsed \? "cursor-pointer hover:opacity-80 transition-opacity" : ""\}`\}'
new_header = 'className={`flex items-center justify-between ${isCollapsed ? "py-5 px-0 justify-center w-full" : "p-5"} border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#111111]/60 ${isCollapsed ? "cursor-pointer hover:opacity-80 transition-opacity" : ""}`}'
content = re.sub(old_header, new_header, content)

with open(filename, 'w') as f:
    f.write(content)
