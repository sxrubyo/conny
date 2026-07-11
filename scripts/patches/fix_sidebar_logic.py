import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

# Update logo area to be clickable when collapsed
old_logo = """        <div className={`p-4 flex items-center ${isCollapsed ? "justify-center" : "justify-between"}`}>
          <div className="flex items-center gap-2">
            <div className="bg-red-700 dark:bg-red-600 w-8 h-8 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-lg leading-none mt-1">C</span>
            </div>
            {!isCollapsed && (
              <span className="font-semibold text-lg text-neutral-900 dark:text-white tracking-tight">Bublee</span>
            )}
          </div>
        </div>"""

new_logo = """        <div 
          className={`p-4 flex items-center ${isCollapsed ? "justify-center cursor-pointer hover:opacity-80 transition-opacity" : "justify-between"}`}
          onClick={isCollapsed ? onToggleCollapse : undefined}
        >
          <div className="flex items-center gap-2">
            <div className="bg-red-700 dark:bg-red-600 w-8 h-8 rounded flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-lg leading-none mt-1">C</span>
            </div>
            {!isCollapsed && (
              <span className="font-semibold text-lg text-neutral-900 dark:text-white tracking-tight">Bublee</span>
            )}
          </div>
        </div>"""

content = content.replace(old_logo, new_logo)

# Hide Search, Navigation and Bottom section when collapsed
old_search = """        {/* Search Bar */}
        {!isCollapsed && ("""
new_search = """        {/* Hide everything else if collapsed */}
        {!isCollapsed && (
          <>
            {/* Search Bar */}
            <div className="px-4 py-4">"""

content = content.replace('{/* Search Bar */}\n        {!isCollapsed && (\n          <div className="px-4 py-4">', new_search)

# Now we need to close the <> at the end of the file.
old_end = """          </div>
        </div>
      </div>
    </aside>
  );
}"""

new_end = """          </div>
        </div>
        </>
        )}
      </div>
    </aside>
  );
}"""

# Wait, this might be tricky if the exact spacing doesn't match. 
