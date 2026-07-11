import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Replace hardcoded KPI dates
# <div className="text-neutral-400 dark:text-[#666666] text-[11px] mt-2">From Jun 01,2024 To Jun 29, 2024</div>
kpi_date_str = '<div className="text-neutral-400 dark:text-[#666666] text-[11px] mt-2">From Jun 01,2024 To Jun 29, 2024</div>'

# We can generate this date dynamically in the component
date_logic = """
  const getKpiDateRange = () => {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: '2-digit', year: 'numeric' };
    return `From ${firstDay.toLocaleDateString(undefined, options)} To ${today.toLocaleDateString(undefined, options)}`;
  };
"""

if 'const getKpiDateRange = () => {' not in content:
    content = content.replace('const getHeatmapColor', date_logic + '\n  const getHeatmapColor')
    
content = content.replace(kpi_date_str, '<div className="text-neutral-400 dark:text-[#666666] text-[11px] mt-2">{getKpiDateRange()}</div>')

with open(filename, 'w') as f:
    f.write(content)
