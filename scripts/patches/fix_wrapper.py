import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# First, remove the button and drag handle from inside <Sidebar>
old_sidebar_part = """      <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)}>
        <div
          onMouseDown={handleMouseDown}
          onDoubleClick={() => setSidebarWidth(240)}
          className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
          style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
        />
        <button
          onClick={() => setSidebarWidth(isCollapsed ? 240 : 80)}
          className="hidden md:flex absolute -right-3 top-[26px] z-50 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full p-1 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white shadow-[0_2px_8px_rgba(0,0,0,0.1)] transition-transform hover:scale-110"
        >
          {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </Sidebar>"""

new_sidebar_part = """      <div style={{ position: "relative", gridRow: "1 / -1", height: "100vh" }}>
        <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)} />
        <div
          onMouseDown={handleMouseDown}
          onDoubleClick={() => setSidebarWidth(240)}
          className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
          style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
        />
        <button
          onClick={() => setSidebarWidth(isCollapsed ? 240 : 80)}
          className="hidden md:flex absolute -right-3 top-[26px] z-50 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full p-1 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white shadow-[0_2px_8px_rgba(0,0,0,0.1)] transition-transform hover:scale-110"
        >
          {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </div>"""

content = content.replace(old_sidebar_part, new_sidebar_part)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
