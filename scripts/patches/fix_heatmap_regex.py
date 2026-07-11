import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

pattern = r'<div style=\{\{\s*display: "grid",\s*gridTemplateColumns:\s*"44px repeat\(7, 1fr\)",\s*gap:\s*"1px"\s*\}\}>.*?<\/div>\s*<\/React\.Fragment>\s*\)\)}\s*<\/div>'

new_heatmap = """<div style={{ display: "grid", gridTemplateColumns: "44px repeat(7, 36px)", gap: "2px", justifyContent: "start" }}>
                {/* Empty top-left cell */}
                <div></div>
                {/* Days Headers */}
                {days.map(d => (
                  <div key={d} className="text-center text-[11px] text-neutral-400 dark:text-[#666666] mb-2">{d}</div>
                ))}

                {/* Grid Rows */}
                {hours.map((h, hIndex) => (
                  <React.Fragment key={h}>
                    <div className="flex items-center text-[10px] text-neutral-400 dark:text-[#666666] justify-end pr-3 h-[36px]">{h}</div>
                    {days.map((_, dIndex) => (
                      <div 
                        key={`${dIndex}-${hIndex}`} 
                        className={`rounded-sm ${getHeatmapColor(dIndex, hIndex)} w-[36px] h-[36px]`}
                      />
                    ))}
                  </React.Fragment>
                ))}
              </div>"""

content = re.sub(pattern, new_heatmap, content, flags=re.DOTALL)

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
