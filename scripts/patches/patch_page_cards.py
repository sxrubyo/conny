import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

# 1. Update flags
old_countries = """const countrySales = [
  { flag: '🇬🇧', name: 'United Kingdom', sales: '6.3K' },
  { flag: '🇮🇩', name: 'Indonesia', sales: '5.2K' },
  { flag: '🇲🇾', name: 'Malaysia', sales: '4.7K' },
  { flag: '🇨🇳', name: 'China', sales: '4.5K' },
  { flag: '🇹🇭', name: 'Thailand', sales: '3.2K' },
  { flag: '🇵🇭', name: 'Philippines', sales: '2.9K' },
];"""

new_countries = """const countrySales = [
  { flag: 'gb', name: 'United Kingdom', sales: '6.3K' },
  { flag: 'id', name: 'Indonesia', sales: '5.2K' },
  { flag: 'my', name: 'Malaysia', sales: '4.7K' },
  { flag: 'cn', name: 'China', sales: '4.5K' },
  { flag: 'th', name: 'Thailand', sales: '3.2K' },
  { flag: 'ph', name: 'Philippines', sales: '2.9K' },
];"""
content = content.replace(old_countries, new_countries)

# Render flag images
old_flag_render = """<span className="text-lg">{c.flag}</span>"""
new_flag_render = """<img src={`https://flagcdn.com/w40/${c.flag}.png`} srcSet={`https://flagcdn.com/w80/${c.flag}.png 2x`} width="20" alt={c.name} className="rounded-sm opacity-90" />"""
content = content.replace(old_flag_render, new_flag_render)

# 2. Update KPI cards to have subtle gradients
# We need to inject a specific class per card index
# Currently it is:
# {[ { label: "Total Revenue", ... }, ... ].map((kpi, i) => (
#   <div key={i} className="bg-white dark:bg-[#252525] border border-neutral-200 dark:border-[#333] rounded-xl p-4 ...">

old_kpi_map = """            {[
              { label: "Total Revenue", val: "$24,500", growth: "+12.5%", up: true },
              { label: "Total Order", val: "1,240", growth: "+8.2%", up: true },
              { label: "New customer", val: "320", growth: "-4.3%", up: false },
              { label: "Conversion rate", val: "3.2%", growth: "+2.1%", up: true },
            ].map((kpi, i) => (
              <div key={i} className="bg-white dark:bg-[#252525] border border-neutral-200 dark:border-[#333] rounded-xl p-4 shadow-sm relative group transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] hover:border-red-500/30 dark:hover:border-red-500/30">"""

new_kpi_map = """            {[
              { label: "Total Revenue", val: "$24,500", growth: "+12.5%", up: true, bg: "dark:bg-gradient-to-br dark:from-red-950/20 dark:to-[#161616]/50" },
              { label: "Total Order", val: "1,240", growth: "+8.2%", up: true, bg: "dark:bg-gradient-to-br dark:from-orange-950/20 dark:to-[#161616]/50" },
              { label: "New customer", val: "320", growth: "-4.3%", up: false, bg: "dark:bg-gradient-to-br dark:from-blue-950/20 dark:to-[#161616]/50" },
              { label: "Conversion rate", val: "3.2%", growth: "+2.1%", up: true, bg: "dark:bg-gradient-to-br dark:from-emerald-950/20 dark:to-[#161616]/50" },
            ].map((kpi, i) => (
              <div key={i} className={`bg-white/80 dark:bg-[#1a1a1a]/80 backdrop-blur-md border border-neutral-200 dark:border-[#2a2a2a] rounded-xl p-4 shadow-sm relative group transition-premium hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] hover:border-neutral-300 dark:hover:border-[#444] ${kpi.bg}`}>"""

content = content.replace(old_kpi_map, new_kpi_map)

# 3. Update Chart Colors to red/yellow subtle
content = content.replace('stroke="#991b1b"', 'stroke="#b91c1c" fillOpacity={1} fill="url(#colorSales)"')
content = content.replace('stroke="#7c7cff"', 'stroke="#ca8a04" fillOpacity={1} fill="url(#colorTarget)"')

# Wait, if we use fill="url(#colorSales)", we need an <defs> block inside the chart.
# And we should change <Line> to <Area> or just add Area. The user said "graficos multi color como rojo amarillos... no solido".
# Let's change LineChart to AreaChart.

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
