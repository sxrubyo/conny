import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1 & 2 & 5. Layout changes
old_root = """  return (
    <div className="flex h-screen w-screen bg-neutral-50 dark:bg-[#1a1a1a] overflow-hidden font-sans text-neutral-900 dark:text-[#ffffff] transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] duration-300">
      <Sidebar />"""

new_root = """  return (
    <div className="w-full overflow-x-auto min-h-screen bg-neutral-50 dark:bg-[#1a1a1a]">
      <div 
        className="flex min-h-screen font-sans text-neutral-900 dark:text-[#ffffff] transition-premium duration-300 mx-auto relative"
        style={{ minWidth: 1280, maxWidth: 1440 }}
      >
        <Sidebar />"""

content = content.replace(old_root, new_root)

# We need to add an extra closing div at the end of the return statement
content = re.sub(r'(\s*)<\/div>\s*\)\;\s*\}\s*$', r'\1    </div>\n\1  </div>\n  );\n}', content)

# 4. Replace fixed heights on chart containers with minHeight
# Chart 1 container might be: className="h-[200px]" or h-64 or something.
# Let's see what it is.
with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
