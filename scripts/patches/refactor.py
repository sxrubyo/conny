import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. ROOT LAYOUT
root_old = """  return (
    <div className="w-full overflow-x-auto min-h-screen bg-neutral-50 dark:bg-[#1a1a1a]">
      <div 
        className="flex min-h-screen font-sans text-neutral-900 dark:text-[#ffffff] transition-premium duration-300 w-full relative"
        style={{ minWidth: 1280 }}
      >
        <Sidebar />

      <main className="flex-1 flex flex-col overflow-auto bg-neutral-100 dark:bg-[#161616] transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] duration-300">"""

root_new = """  return (
    <div 
      className="bg-neutral-50 dark:bg-[#1a1a1a] font-sans text-neutral-900 dark:text-[#ffffff] transition-premium duration-300"
      style={{ display: "grid", gridTemplateColumns: "240px 1fr", gridTemplateRows: "auto 1fr", height: "100vh", width: "100%", overflow: "hidden" }}
    >
      <Sidebar />
      <main 
        className="bg-neutral-100 dark:bg-[#161616] transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] duration-300"
        style={{ display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden" }}
      >"""
content = content.replace(root_old, root_new)

# Ensure the end closing divs match what we changed.
# The original had 2 divs closing, now we only have 1 root div. 
# So we need to remove one closing div at the end.
content = re.sub(r'\s*</div>\s*</div>\s*\);\s*}\s*$', r'\n    </div>\n  );\n}', content)

# 2. CONTENT SCROLL AREA
scroll_old = '<div className="flex-1 p-4 lg:p-4 max-w-[1400px] mx-auto w-full animate-premium">'
scroll_new = '<div className="p-4 lg:p-4 animate-premium" style={{ flex: 1, overflowY: "auto", overflowX: "hidden", minWidth: 0 }}>'
content = content.replace(scroll_old, scroll_new)

# 3. KPI CARDS ROW
kpi_old = '<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">'
kpi_new = '<div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }} className="mb-4">'
content = content.replace(kpi_old, kpi_new)

# 4. MIDDLE ROW
middle_old = '<div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">'
middle_new = '<div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }} className="mb-4">'
content = content.replace(middle_old, middle_new)

# 5. BOTTOM ROW
bottom_old = '<div className="flex flex-col gap-4">'
bottom_new = '<div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.6fr)", gap: 12 }}>'
content = content.replace(bottom_old, bottom_new)

# 6. RECHARTS ResponsiveContainer
recharts_old = """              <div className="min-h-[220px] flex-1 w-full">
                <ResponsiveContainer width="100%" height="100%">"""
recharts_new = """              <div style={{ width: "100%", minWidth: 0 }}>
                <ResponsiveContainer width="100%" height={220}>"""
content = content.replace(recharts_old, recharts_new)

# 7. HEATMAP GRID
heatmap_old = r'<div className="flex min-w-\[350px\]">.*?<\/div>\s*<\/div>\s*<\/div>'
heatmap_new = """              <div style={{ display: "grid", gridTemplateColumns: "44px repeat(7, 1fr)", gap: "1px" }}>
                {/* Empty top-left cell */}
                <div></div>
                {/* Days Headers */}
                {days.map(d => (
                  <div key={d} className="text-center text-[11px] text-neutral-400 dark:text-[#666666] mb-2">{d}</div>
                ))}
                
                {/* Grid Rows */}
                {hours.map((h, hIndex) => (
                  <React.Fragment key={h}>
                    <div className="flex items-center text-[10px] text-neutral-400 dark:text-[#666666] justify-end pr-3" style={{ height: "100%", minHeight: 0 }}>{h}</div>
                    {days.map((_, dIndex) => (
                      <div 
                        key={`${dIndex}-${hIndex}`} 
                        className={`rounded-sm ${getHeatmapColor(dIndex, hIndex)}`}
                        style={{ width: "100%", aspectRatio: "1" }}
                      />
                    ))}
                  </React.Fragment>
                ))}
              </div>"""
content = re.sub(heatmap_old, heatmap_new, content, flags=re.DOTALL)


with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
