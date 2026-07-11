import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Replace interface SidebarProps
old_props = """interface SidebarProps {
  className?: string;
  children?: React.ReactNode;
}"""
new_props = """interface SidebarProps {
  className?: string;
  children?: React.ReactNode;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}"""
content = content.replace(old_props, new_props)

# Fix Sidebar definition
old_def = 'export function Sidebar({ className = "", children }: SidebarProps) {'
new_def = 'export function Sidebar({ className = "", children, isCollapsed = false, onToggleCollapse }: SidebarProps) {'
content = content.replace(old_def, new_def)

# Remove local state for isCollapsed
content = re.sub(r'const \[isCollapsed, setIsCollapsed\] = useState\(false\);\n\s*const toggleCollapse = \(\) => setIsCollapsed\(!isCollapsed\);', '', content)

# Find the collapse button and reposition it completely out of the flex row, using absolute positioning
old_header = """        <div className="flex items-center justify-between p-5 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#111111]/60">
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center">
                <img
                    src="/dev-portal/isotype.png"
                    alt="Bublee"
                    className="w-full h-full object-contain brightness-0 opacity-80 dark:invert dark:opacity-70"
                />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-neutral-900 dark:text-white text-base">Santiago</span>
                <span className="text-xs text-neutral-500 dark:text-neutral-600 dark:text-neutral-400">Workspace</span>
              </div>
            </div>
          )}

          {isCollapsed && (
            <div className="w-9 h-9 rounded-lg flex items-center justify-center mx-auto">
                <img
                    src="/dev-portal/isotype.png"
                    alt="Bublee"
                    className="w-full h-full object-contain brightness-0 opacity-80 dark:invert dark:opacity-70"
                />
            </div>
          )}

          <button
            onClick={toggleCollapse}
            className="hidden md:flex p-1.5 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-200 dark:bg-neutral-800 transition-all duration-200 text-neutral-600 dark:text-neutral-400 hover:text-white"
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>"""

new_header = """        <div className={`flex items-center p-5 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#111111]/60 ${isCollapsed ? "justify-center" : "justify-start"}`}>
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center">
                <img
                    src="/dev-portal/isotype.png"
                    alt="Bublee"
                    className="w-full h-full object-contain brightness-0 opacity-80 dark:invert dark:opacity-70"
                />
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="font-semibold text-neutral-900 dark:text-white text-base truncate">Santiago</span>
                <span className="text-xs text-neutral-500 dark:text-neutral-600 dark:text-neutral-400 truncate">Workspace</span>
              </div>
            </div>
          )}

          {isCollapsed && (
            <div className="w-9 h-9 rounded-lg flex items-center justify-center">
                <img
                    src="/dev-portal/isotype.png"
                    alt="Bublee"
                    className="w-full h-full object-contain brightness-0 opacity-80 dark:invert dark:opacity-70"
                />
            </div>
          )}
        </div>

        {/* Absolute floating button outside the sidebar bounds */}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="hidden md:flex absolute -right-3 top-[22px] z-50 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full p-1 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white shadow-sm transition-transform hover:scale-110"
          >
            {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
          </button>
        )}"""

content = content.replace(old_header, new_header)

# In case `toggleCollapse` is used elsewhere in the file, replace it with `onToggleCollapse`
content = content.replace('onClick={toggleCollapse}', 'onClick={onToggleCollapse}')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
