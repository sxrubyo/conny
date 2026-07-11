import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Add sidebarWidth state
state_old = """  const [greeting, setGreeting] = useState<string>("Dashboard");
  const [isDark, setIsDark] = useState(true);"""
state_new = """  const [greeting, setGreeting] = useState<string>("Dashboard");
  const [isDark, setIsDark] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(240);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = startWidth + (moveEvent.clientX - startX);
      setSidebarWidth(Math.min(360, Math.max(180, newWidth)));
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };"""
content = content.replace(state_old, state_new)

# 2. Update gridTemplateColumns
grid_old = 'gridTemplateColumns: "240px 1fr"'
grid_new = 'gridTemplateColumns: `${sidebarWidth}px 1fr`'
content = content.replace(grid_old, grid_new)

# 3. Add drag handle as child of Sidebar
sidebar_old = "<Sidebar />"
sidebar_new = """      <Sidebar>
        <div 
          onMouseDown={handleMouseDown}
          onDoubleClick={() => setSidebarWidth(240)}
          className="hover:bg-[#e05a2b]/30 transition-colors duration-150"
          style={{ position: "absolute", right: 0, top: 0, width: 4, height: "100%", cursor: "col-resize", zIndex: 10, background: "transparent" }}
        />
      </Sidebar>"""
content = content.replace(sidebar_old, sidebar_new)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)

