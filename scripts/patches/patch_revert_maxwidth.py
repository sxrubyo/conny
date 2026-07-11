with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

old_layout = """      <div 
        className="flex min-h-screen font-sans text-neutral-900 dark:text-[#ffffff] transition-premium duration-300 mx-auto relative"
        style={{ minWidth: 1280, maxWidth: 1440 }}
      >"""

new_layout = """      <div 
        className="flex min-h-screen font-sans text-neutral-900 dark:text-[#ffffff] transition-premium duration-300 w-full relative"
        style={{ minWidth: 1280 }}
      >"""

content = content.replace(old_layout, new_layout)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
