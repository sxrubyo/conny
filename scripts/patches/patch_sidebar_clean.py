with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# I will replace the entire "User Profile and Help Center" section.
import re

# Find the block from `{/* User Profile and Help Center */}` to the end of that flex container.
# It ends with `</button>` (or `</div>` if I changed it previously).

new_bottom_section = """        {/* Clean Profile and Help Center */}
        <div className="mt-auto px-4 pb-6 flex flex-col gap-4">
          {/* Profile Area - Clickable to /settings */}
          <div 
            onClick={() => handleItemClick("settings", "/settings")}
            className={`flex items-center cursor-pointer group ${isCollapsed ? "justify-center" : "justify-start"}`}
            title="Settings & Profile"
          >
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 flex items-center justify-center flex-shrink-0 overflow-hidden shadow-sm">
                {/* Clean avatar with initials or image */}
                <span className="text-xs font-bold text-neutral-600 dark:text-neutral-300">SR</span>
            </div>
            
            {!isCollapsed && (
                <div className="ml-3 flex flex-col min-w-0">
                  <span className="text-sm font-semibold text-neutral-900 dark:text-white truncate group-hover:text-red-700 dark:group-hover:text-red-500 transition-colors">Santiago</span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">Santi21435@gmail.com</span>
                </div>
            )}
          </div>

          {/* Help Center - Below Profile, Clean text no border */}
          <div
            onClick={() => handleItemClick("help", "/help")}
            className={`flex items-center cursor-pointer group text-neutral-500 hover:text-neutral-900 dark:hover:text-white transition-colors ${isCollapsed ? "justify-center" : "justify-start"}`}
            title="Help Center"
          >
            <HelpCircle className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && (
              <span className="ml-3 text-xs font-medium">Help Center</span>
            )}
          </div>
          
          {/* Theme Toggle - Clean Text No Square */}
          <div
            onClick={toggleTheme}
            className={`flex items-center cursor-pointer group text-neutral-500 hover:text-neutral-900 dark:hover:text-white transition-colors ${isCollapsed ? "justify-center" : "justify-start"}`}
            title="Toggle Theme"
          >
            {isThemeDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {!isCollapsed && (
              <span className="ml-3 text-xs font-medium">{isThemeDark ? "Light Mode" : "Dark Mode"}</span>
            )}
          </div>
        </div>
      </div>
    </aside>
"""

# Let's use regex to replace everything from `{/* User Profile and Help Center */}` to `</aside>`
content = re.sub(r'\{\/\* User Profile and Help Center \*\/\}[\s\S]*?<\/aside>', new_bottom_section, content)

# I should also make sure to remove any other profile blocks if they exist.
# The code was patched before, let's just do a manual string replace if regex is too risky.
with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
