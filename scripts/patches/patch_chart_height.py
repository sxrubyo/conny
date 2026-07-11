with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Make the card flex and replace h-[220px] with min-h-[220px] flex-1
old_chart_card = """            {/* AreaChart */}
            <div className="bg-white dark:bg-[#252525] border border-neutral-200 dark:border-[#333] rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-4">"""

new_chart_card = """            {/* AreaChart */}
            <div className="bg-white dark:bg-[#252525] border border-neutral-200 dark:border-[#333] rounded-xl p-4 shadow-sm flex flex-col flex-1">
              <div className="flex items-center justify-between mb-4">"""
content = content.replace(old_chart_card, new_chart_card)

content = content.replace('className="h-[220px] w-full"', 'className="min-h-[220px] flex-1 w-full"')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
