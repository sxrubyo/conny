with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Update Title and Subtitle
old_header = """<h1 className="text-3xl lg:text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
                {greeting.split('Santiago').map((part, i, arr) => (
                  <React.Fragment key={i}>
                    {part}
                    {i < arr.length - 1 && (
                      <span className={`${caveat.className} text-[#b91c1c] text-4xl lg:text-5xl font-normal mx-1`}>Santiago</span>
                    )}
                  </React.Fragment>
                ))}
              </h1>
              <p className="text-neutral-500 dark:text-[#888888] text-base mt-2">Resumen general de rendimiento</p>"""

new_header = """<h1 className="text-4xl lg:text-5xl font-bold text-neutral-900 dark:text-white tracking-tight leading-tight">
                {greeting.split('Santiago').map((part, i, arr) => (
                  <React.Fragment key={i}>
                    {part}
                    {i < arr.length - 1 && (
                      <span className={`${caveat.className} text-[#b91c1c] text-6xl lg:text-7xl font-normal mx-1 tracking-normal`}>Santiago</span>
                    )}
                  </React.Fragment>
                ))}
              </h1>
              <p className="text-neutral-500 dark:text-[#888888] text-lg lg:text-xl mt-3 font-medium">Resumen general de rendimiento</p>"""

content = content.replace(old_header, new_header)

# 2. Update Heatmap gap
old_heatmap = """<div className="flex-1 grid grid-cols-7 gap-1">"""
new_heatmap = """<div className="flex-1 grid grid-cols-7 gap-[2px]">"""

content = content.replace(old_heatmap, new_heatmap)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
