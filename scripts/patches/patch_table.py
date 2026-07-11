with open('/home/ubuntu/bublee-dev-react/src/components/ui/table-with-dialog.tsx', 'r') as f:
    content = f.read()

# Change container background to match sidebar (bg-neutral-50 dark:bg-[#111111])
content = content.replace('bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl shadow-sm mt-8',
                          'bg-neutral-50 dark:bg-[#111111] border border-neutral-200 dark:border-[#333333] rounded-xl shadow-sm mt-8')

# Change TableHeader background (sticky)
content = content.replace('bg-white dark:bg-neutral-900 z-10 shadow-sm',
                          'bg-neutral-50 dark:bg-[#111111] z-10 shadow-sm')

# Change TableFooter background (sticky)
content = content.replace('bg-neutral-50 dark:bg-neutral-900 z-10 border-t border-neutral-200 dark:border-neutral-800',
                          'bg-neutral-50 dark:bg-[#111111] z-10 border-t border-neutral-200 dark:border-[#333333]')

# Change TableRow hover to dark red
content = content.replace('hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors',
                          'hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors')

# Change Checkbox checked state to dark red
content = content.replace('data-[state=checked]:bg-neutral-900 dark:data-[state=checked]:bg-neutral-100 data-[state=checked]:text-white dark:data-[state=checked]:text-neutral-900',
                          'data-[state=checked]:bg-red-900 data-[state=checked]:text-white data-[state=checked]:border-red-900')

# Change Details button hover to dark red
content = content.replace('hover:bg-neutral-100 dark:hover:bg-neutral-800',
                          'hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-900 dark:hover:text-red-200 hover:border-red-900/50')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/table-with-dialog.tsx', 'w') as f:
    f.write(content)
