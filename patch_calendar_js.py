import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

calendar_logic = """
// ── Calendar View Logic ──
let currentCalendarDate = new Date();
let globalAppointmentsList = [];

const calendarGridContent = document.getElementById('calendar-grid-content');
const calendarMonthTitle = document.getElementById('calendar-month-title');
const calendarPrevBtn = document.getElementById('calendar-prev-btn');
const calendarNextBtn = document.getElementById('calendar-next-btn');
const calendarTodayCount = document.getElementById('calendar-today-count');

if (calendarPrevBtn) {
    calendarPrevBtn.addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
        renderCalendarGrid();
    });
}
if (calendarNextBtn) {
    calendarNextBtn.addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
        renderCalendarGrid();
    });
}

function renderCalendarGrid() {
    if (!calendarGridContent) return;
    
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    
    const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    if (calendarMonthTitle) calendarMonthTitle.textContent = `${monthNames[month]} ${year}`;
    
    // Calculate days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    calendarGridContent.innerHTML = '';
    
    // Previous month padding
    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--surface)';
        cell.style.opacity = '0.5';
        cell.style.padding = '8px';
        calendarGridContent.appendChild(cell);
    }
    
    // Today check
    const today = new Date();
    let todayCount = 0;
    
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const cellDate = new Date(year, month, day);
        const dateString = cellDate.toISOString().split('T')[0];
        
        const cell = document.createElement('div');
        cell.style.background = 'var(--surface)';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.overflowY = 'auto';
        
        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());
        
        // Day number
        const dayNumber = document.createElement('div');
        dayNumber.textContent = day;
        dayNumber.style.fontWeight = isToday ? 'bold' : 'normal';
        dayNumber.style.color = isToday ? '#fff' : 'var(--text-muted)';
        dayNumber.style.backgroundColor = isToday ? 'var(--primary)' : 'transparent';
        dayNumber.style.width = '24px';
        dayNumber.style.height = '24px';
        dayNumber.style.borderRadius = '50%';
        dayNumber.style.display = 'flex';
        dayNumber.style.alignItems = 'center';
        dayNumber.style.justifyContent = 'center';
        dayNumber.style.marginBottom = '4px';
        cell.appendChild(dayNumber);
        
        // Find appointments for this day
        const dayAppointments = globalAppointmentsList.filter(apt => {
            if (!apt.datetime_slot) return false;
            return apt.datetime_slot.startsWith(dateString);
        });
        
        if (isToday) todayCount = dayAppointments.length;
        
        // Render appointments inside the cell
        dayAppointments.forEach(apt => {
            const aptEl = document.createElement('div');
            aptEl.style.background = apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)';
            aptEl.style.borderLeft = `3px solid ${apt.status === 'confirmada' ? '#10b981' : 'var(--primary)'}`;
            aptEl.style.padding = '4px 6px';
            aptEl.style.borderRadius = '0 4px 4px 0';
            aptEl.style.fontSize = '11px';
            aptEl.style.color = 'var(--text)';
            aptEl.style.marginBottom = '2px';
            aptEl.style.cursor = 'pointer';
            aptEl.title = `Estado: ${apt.status}\\nServicio: ${apt.service || 'General'}`;
            
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente';
            
            aptEl.innerHTML = `<strong style="color:var(--text);">${aptTime}</strong> - ${aptName}`;
            cell.appendChild(aptEl);
        });
        
        calendarGridContent.appendChild(cell);
    }
    
    // Next month padding
    const totalCells = firstDay + daysInMonth;
    const remainingCells = (7 - (totalCells % 7)) % 7;
    for (let i = 0; i < remainingCells; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--surface)';
        cell.style.opacity = '0.5';
        cell.style.padding = '8px';
        calendarGridContent.appendChild(cell);
    }
    
    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;
}

// Modify existing renderAppointments to also render the calendar
const originalRenderAppointments = renderAppointments;
renderAppointments = function(list) {
    globalAppointmentsList = list;
    originalRenderAppointments(list);
    renderCalendarGrid();
};
"""

js = js + "\n" + calendar_logic

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
