with open('/home/ubuntu/bublee-dev-react/src/components/ui/table-with-dialog.tsx', 'r') as f:
    content = f.read()

# Make table more compact
content = content.replace('p-6', 'p-4')
content = content.replace('text-lg', 'text-sm') # Header title
content = content.replace('max-h-[400px]', 'max-h-[300px]')
content = content.replace('text-sm text-neutral-500', 'text-xs text-neutral-500')
content = content.replace('pl-6', 'pl-4')

with open('/home/ubuntu/bublee-dev-react/src/components/ui/table-with-dialog.tsx', 'w') as f:
    f.write(content)
