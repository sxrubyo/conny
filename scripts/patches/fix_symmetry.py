with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Change the grid for bottom row to make it full width for both or split
# Currently: <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
# Let's change it to a normal flex column or grid with 1 column, so each takes full width.
content = content.replace('<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">', '<div className="flex flex-col gap-6">')
content = content.replace('<div className="lg:col-span-2">', '<div className="w-full">')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
