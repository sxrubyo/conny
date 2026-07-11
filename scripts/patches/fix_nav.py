import re

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'r') as f:
    content = f.read()

old_button = """                  <button
                    onClick={() => handleItemClick(item.id, item.href)}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200 group
                      ${isActive
                        ? "bg-red-50 dark:bg-red-900/10 text-red-700 dark:text-red-500"
                        : "text-neutral-600 dark:text-neutral-400 hover:bg-white dark:bg-neutral-900 hover:text-neutral-200"
                      }
                      ${isCollapsed ? "justify-center px-2" : ""}
                    `}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <div className="flex items-center justify-center min-w-[24px]">
                      <Icon className={`h-5 w-5 flex-shrink-0 ${isActive ? "text-red-700 dark:text-red-500" : "text-neutral-500 dark:text-neutral-600 dark:text-neutral-400 group-hover:text-neutral-700 dark:text-neutral-300"}`} />
                    </div>

                    {!isCollapsed && (
                      <div className="flex items-center justify-between w-full">
                        <span className={`text-sm ${isActive ? "font-medium" : "font-normal"}`}>{item.name}</span>"""

new_button = """                  <button
                    onClick={() => handleItemClick(item.id, item.href)}
                    className={`
                      w-full flex items-center space-x-3 py-2 rounded-r-md text-left transition-all duration-150 group border-l-2
                      ${isActive
                        ? "border-[#e05a2b] text-[#e05a2b] bg-transparent"
                        : "border-transparent text-neutral-600 dark:text-[#666666] hover:bg-neutral-100 dark:hover:bg-white/5"
                      }
                      ${isCollapsed ? "justify-center px-2 border-l-0" : "pl-[10px] pr-3"}
                    `}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <div className="flex items-center justify-center min-w-[24px]">
                      <Icon className={`h-5 w-5 flex-shrink-0 ${isActive ? "text-[#e05a2b]" : "text-neutral-500 dark:text-[#666666] group-hover:text-neutral-700 dark:group-hover:text-white"}`} />
                    </div>

                    {!isCollapsed && (
                      <div className="flex items-center justify-between w-full">
                        <span className={`text-sm ${isActive ? "font-medium" : "font-normal"}`}>{item.name}</span>"""

content = content.replace(old_button, new_button)

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)

