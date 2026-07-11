with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Make the profile section clickable
old_profile = """          <div className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between"}`}>
            <div className="flex items-center min-w-0">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 flex items-center justify-center flex-shrink-0">"""

new_profile = """          <button 
            onClick={() => handleItemClick("settings", "/settings")}
            className={`flex items-center w-full text-left p-1.5 -ml-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800/50 transition-colors ${isCollapsed ? "justify-center" : "justify-between"}`}
            title="Settings & Profile"
          >
            <div className="flex items-center min-w-0">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 flex items-center justify-center flex-shrink-0">"""

content = content.replace(old_profile, new_profile)

# Also need to replace the closing div of the old_profile flex container with </button>
# Let's find it. It's after the theme toggle button.
#                 <div
#                     onClick={toggleTheme}
# ...
#                     {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
#                 </div>
#             )}
#           </div>

import re
content = re.sub(r'\{isDark \? <Sun className="h-4 w-4" \/> : <Moon className="h-4 w-4" \/>\}\s*<\/div>\s*\)\}\s*<\/div>', '{isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}\n                </div>\n            )}\n          </button>', content)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
