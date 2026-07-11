with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# Update Tooltip colors
content = content.replace('text-[#991b1b]', 'text-[#b91c1c]')
content = content.replace('text-[#7c7cff]', 'text-[#ca8a04]')
# Update Legend dot colors
content = content.replace('bg-[#991b1b]', 'bg-[#b91c1c]')
content = content.replace('bg-[#7c7cff]', 'bg-[#ca8a04]')
content = content.replace('border-[#7c7cff]', 'border-[#ca8a04]')

# Change LineChart to AreaChart
content = content.replace('LineChart', 'AreaChart')
content = content.replace('Line,', 'Area,')
content = content.replace('<Line ', '<Area ')
content = content.replace('</Line>', '</Area>')

# Insert defs for gradients
defs_block = """                  <AreaChart data={lineChartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#b91c1c" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#b91c1c" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorTarget" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ca8a04" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ca8a04" stopOpacity={0}/>
                      </linearGradient>
                    </defs>"""
content = content.replace('<AreaChart data={lineChartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>', defs_block)

# Clean up Area activeDot fill to match
content = content.replace("activeDot={{ r: 4, fill: '#991b1b', strokeWidth: 0 }}", "activeDot={{ r: 4, fill: '#b91c1c', strokeWidth: 0 }}")
content = content.replace("activeDot={{ r: 4, fill: '#7c7cff', strokeWidth: 0 }}", "activeDot={{ r: 4, fill: '#ca8a04', strokeWidth: 0 }}")

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
