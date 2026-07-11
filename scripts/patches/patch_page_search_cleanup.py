import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Remove the old search block
old_search_block = """              {/* Search */}
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Search"
                  className="w-full bg-white dark:bg-[#2e2e2e] border border-neutral-200 dark:border-[#333] rounded-full py-2 pl-10 pr-4 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-[#991b1b]"
                />
              </div>"""

content = content.replace(old_search_block, "              {/* Expanding Search */}\n              <ExpandingSearchDock placeholder=\"Search...\" />")

# Remove the one I injected earlier
injected_search = """              {/* Expanding Search */}
              <div className="hidden sm:block">
                <ExpandingSearchDock placeholder="Search performance..." />
              </div>

"""
content = content.replace(injected_search, "")

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
