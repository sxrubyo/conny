import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Make cells white (bg-main), no internal border logic (gap handles it), smaller minHeight (100px)
# Header cells
js = js.replace("th.style.padding = '8px';\n        th.style.borderBottom = '1px solid var(--border-color)';", "th.style.padding = '10px 8px';\n        th.style.background = 'var(--bg-main)';")

# Padding cells
js = js.replace("cell.style.background = 'transparent';\n        cell.style.minHeight = '120px';", "cell.style.background = 'var(--bg-panel)';\n        cell.style.minHeight = '100px';")

# Actual Day cells
old_cell_style = """        cell.style.background = 'var(--bg-main)';
        cell.style.border = '1px solid var(--border-color)';
        cell.style.borderRadius = '6px';
        cell.style.minHeight = '120px';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';
        cell.style.transition = 'box-shadow 0.2s';
        
        cell.addEventListener('mouseover', () => { cell.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'; cell.style.borderColor = 'var(--accent-color)'; });
        cell.addEventListener('mouseout', () => { cell.style.boxShadow = 'none'; cell.style.borderColor = 'var(--border-color)'; });"""

new_cell_style = """        cell.style.background = 'var(--bg-main)';
        cell.style.minHeight = '100px';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';"""

js = js.replace(old_cell_style, new_cell_style)

# Day number style
old_number_style = """        const dayNumber = document.createElement('div');
        dayNumber.textContent = day;
        dayNumber.style.fontSize = '14px';
        dayNumber.style.width = '28px';
        dayNumber.style.height = '28px';
        dayNumber.style.display = 'flex';
        dayNumber.style.alignItems = 'center';
        dayNumber.style.justifyContent = 'center';
        dayNumber.style.borderRadius = '50%';
        dayNumber.style.fontWeight = isToday ? '700' : '500';
        
        if (isToday) {
            dayNumber.style.color = 'var(--accent-color)';
            dayNumber.style.background = 'rgba(139, 92, 246, 0.15)';
        } else {
            dayNumber.style.color = 'var(--text-primary)';
        }"""

new_number_style = """        const dayNumber = document.createElement('div');
        dayNumber.textContent = day;
        dayNumber.style.fontSize = '12px';
        dayNumber.style.minWidth = '24px';
        dayNumber.style.height = '24px';
        dayNumber.style.padding = '0 6px';
        dayNumber.style.display = 'flex';
        dayNumber.style.alignItems = 'center';
        dayNumber.style.justifyContent = 'center';
        dayNumber.style.borderRadius = '6px';
        dayNumber.style.border = '1px solid var(--border-color)';
        dayNumber.style.fontWeight = isToday ? '700' : '600';
        
        if (isToday) {
            dayNumber.style.color = '#ffffff';
            dayNumber.style.background = 'var(--accent-color)';
            dayNumber.style.borderColor = 'var(--accent-color)';
        } else {
            dayNumber.style.color = 'var(--text-primary)';
            dayNumber.style.background = 'var(--bg-main)';
        }"""

js = js.replace(old_number_style, new_number_style)

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
