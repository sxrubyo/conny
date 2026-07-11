import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

new_bottom = """        {/* Clean Profile, Help Center and Theme Toggle */}
        <div className="mt-auto px-4 pb-6 flex flex-col gap-5 pt-4 border-t border-neutral-200 dark:border-neutral-800/50">
          
          {/* Profile Area - Clickable to /settings */}
          <div 
            onClick={() => window.location.href = '/settings'}
            className={`flex items-center cursor-pointer group ${isCollapsed ? "justify-center" : "justify-start"}`}
            title="Settings & Profile"
          >
            <div className="h-9 w-9 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 shadow-sm">
                <img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover" />
            </div>
            
            {!isCollapsed && (
                <div className="ml-3 flex flex-col min-w-0">
                  <span className="text-sm font-semibold text-neutral-900 dark:text-white truncate group-hover:text-red-700 dark:group-hover:text-red-500 transition-colors">Santiago</span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">Santi21435@gmail.com</span>
                </div>
            )}
          </div>

          {/* Help Center - Clean text no border */}
          <div
            onClick={() => window.location.href = '/help'}
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
      </>
  );
}"""

content = re.sub(r'\{\/\* Bottom section with profile \*\/\}[\s\S]*?\)\;\n\}', new_bottom, content)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
