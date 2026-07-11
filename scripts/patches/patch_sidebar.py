with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# 1. Reduce Sidebar Width
content = content.replace('w-64', 'w-56')

# 2. Adjust active item color (less red, more subtle)
content = content.replace('bg-red-900 text-white', 'bg-red-50 dark:bg-red-900/10 text-red-700 dark:text-red-500')
# Fix the text-white inside the icon for active state
content = content.replace('${isActive ? "text-white" : "text-neutral-500', '${isActive ? "text-red-700 dark:text-red-500" : "text-neutral-500')

# 3. Add Help Center above User Profile
profile_block = """        {/* User Profile and Help Center */}
        <div className="border-t border-neutral-200 dark:border-neutral-800 p-3 flex flex-col gap-2">
          {!isCollapsed ? (
            <button className="flex items-center space-x-3 px-2 py-2 rounded-lg text-left transition-all duration-300 text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/50 group">
              <HelpCircle className="h-4 w-4 flex-shrink-0" />
              <span className="text-xs font-medium">Help Center</span>
            </button>
          ) : (
            <button className="flex items-center justify-center p-2 rounded-lg transition-all duration-300 text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/50 group" title="Help Center">
              <HelpCircle className="h-4 w-4" />
            </button>
          )}

          <div className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between"}`}>
            <div className="flex items-center min-w-0">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 flex items-center justify-center flex-shrink-0">
"""

# Replace the existing User Profile top part
import re
content = re.sub(r'\{\/\* User Profile \*\/\}\s*<div className="border-t border-neutral-200 dark:border-neutral-800 p-4">\s*<div className={`flex items-center \$\{isCollapsed \? "justify-center" : "justify-between"\} `}>\s*<div className="flex items-center min-w-0">\s*<div className="h-9 w-9 rounded-full bg-gradient-to-br from-neutral-200 to-neutral-300 dark:from-neutral-700 dark:to-neutral-800 flex items-center justify-center flex-shrink-0">', profile_block, content)

# 4. Text sizes and padding reductions in Sidebar
content = content.replace('text-sm font-medium', 'text-xs font-medium')
content = content.replace('text-sm font-normal', 'text-xs font-normal')
content = content.replace('text-2xl font-bold', 'text-xl font-bold') # For logo text
content = content.replace('h-6 w-6', 'h-5 w-5') # For logo icon
content = content.replace('h-9 w-9', 'h-8 w-8') # Profile pic size

# Make sure HelpCircle is imported
if 'HelpCircle' not in content:
    content = content.replace('import {', 'import {\n  HelpCircle,')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
