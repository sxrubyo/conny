import re

filename = '/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# I will replace hardcoded colors with tailwind classes that support light and dark.
# bg-[#161616] -> bg-neutral-50 dark:bg-[#161616]
content = content.replace('bg-[#161616]', 'bg-neutral-50 dark:bg-[#161616]')
# text-white -> text-neutral-900 dark:text-white
content = content.replace('text-white', 'text-neutral-900 dark:text-white')
# bg-[#1e1e1e] -> bg-white dark:bg-[#1e1e1e]
content = content.replace('bg-[#1e1e1e]', 'bg-white dark:bg-[#1e1e1e]')
# border-[#2a2a2a] -> border-neutral-200 dark:border-[#2a2a2a]
content = content.replace('border-[#2a2a2a]', 'border-neutral-200 dark:border-[#2a2a2a]')
# bg-[#252525] -> bg-neutral-50 dark:bg-[#252525]
content = content.replace('bg-[#252525]', 'bg-neutral-50 dark:bg-[#252525]')
# border-[#333] -> border-neutral-200 dark:border-[#333]
content = content.replace('border-[#333]', 'border-neutral-200 dark:border-[#333]')
# text-[#888] -> text-neutral-500 dark:text-[#888]
content = content.replace('text-[#888]', 'text-neutral-500 dark:text-[#888]')
# text-[#666] -> text-neutral-400 dark:text-[#666]
content = content.replace('text-[#666]', 'text-neutral-400 dark:text-[#666]')

with open(filename, 'w') as f:
    f.write(content)
