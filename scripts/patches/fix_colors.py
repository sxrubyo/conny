with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Change View All button color
content = content.replace('text-[#e05a2b]', 'text-red-700 dark:text-red-500')

# Change hover color on Sales by Country cards
content = content.replace('hover:bg-neutral-100 dark:hover:bg-[#2e2e2e]', 'hover:bg-red-50 dark:hover:bg-red-900/20')

# Also, in the LineChart, they had #e05a2b, let's change it to #991b1b (red-800) to match "rojo oscuro"
content = content.replace('#e05a2b', '#991b1b')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
