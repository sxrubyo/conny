import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Update grid style
old_grid = 'style={{ display: "grid", gridTemplateColumns: `${sidebarWidth}px 1fr`, gridTemplateRows: "1fr", height: "100vh", width: "100%", overflow: "hidden" }}'
new_grid = 'style={{ display: "grid", gridTemplateColumns: `${isCollapsed ? 52 : sidebarWidth}px 1fr`, gridTemplateRows: "1fr", height: "100vh", width: "100%", overflow: "hidden", transition: "grid-template-columns 0.2s ease" }}'
content = content.replace(old_grid, new_grid)

# Replace the whole wrapper
pattern = r'<div style=\{\{ position: "relative", gridRow: "1 / -1", height: "100vh" \}\}>.*?<\/div>'

new_wrapper = """<div style={{ position: "relative", gridRow: "1 / -1", height: "100vh" }}>
        <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 52)} />
        {!isCollapsed && (
          <>
            <div
              onMouseDown={handleMouseDown}
              onDoubleClick={() => setSidebarWidth(240)}
              className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
              style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
            />
            <button
              onClick={() => setSidebarWidth(52)}
              className="hidden md:flex absolute -right-3 top-[26px] z-50 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full p-1 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white shadow-[0_2px_8px_rgba(0,0,0,0.1)] transition-transform hover:scale-110"
            >
              <ChevronLeft className="h-3 w-3" />
            </button>
          </>
        )}
      </div>"""

content = re.sub(pattern, new_wrapper, content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
