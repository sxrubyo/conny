import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Remove the absolute button from Sidebar completely
pattern = r'\{\/\* Absolute floating button outside the sidebar bounds \*\/\}.*?<\/button>\n\s*\)\}'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)


with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Replace Sidebar invocation to include the toggle button next to the drag handle
old_sidebar_part = """      <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)}>
        <div
          onMouseDown={handleMouseDown}
          onDoubleClick={() => setSidebarWidth(240)}
          className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
          style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
        />
      </Sidebar>"""

new_sidebar_part = """      <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)}>
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

content = content.replace(old_sidebar_part, new_sidebar_part)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
