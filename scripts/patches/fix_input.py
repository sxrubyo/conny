import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/input.tsx'
with open(filename, 'r') as f:
    content = f.read()

content = content.replace(
    'bg-background px-3 py-2 text-sm text-foreground shadow-sm shadow-black/5 transition-shadow placeholder:text-muted-foreground/70 focus-visible:border-ring',
    'bg-white dark:bg-neutral-900 px-3 py-2 text-sm text-neutral-900 dark:text-white shadow-sm shadow-black/5 transition-shadow placeholder:text-neutral-500 dark:placeholder:text-neutral-400 focus-visible:border-neutral-400 dark:focus-visible:border-neutral-600'
)

content = content.replace(
    'border border-input',
    'border border-neutral-200 dark:border-neutral-800'
)

content = content.replace(
    'focus-visible:ring-ring/20',
    'focus-visible:ring-neutral-400/20 dark:focus-visible:ring-neutral-600/20'
)

with open(filename, 'w') as f:
    f.write(content)
