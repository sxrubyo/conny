import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Currently page.tsx has:
old_sidebar = """        <Sidebar isCollapsed={isCollapsed} onToggleCollapse={() => setSidebarWidth(isCollapsed ? 240 : 80)}>
        <div
          onMouseDown={handleMouseDown}
          onDoubleClick={() => setSidebarWidth(240)}
          className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
          style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
        />
      </Sidebar>"""

# Wait, let's look at the exact spacing first.
