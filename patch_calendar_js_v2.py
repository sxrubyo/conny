import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Replace the renderCalendarGrid function block. 
# We need to find the definition of `function renderCalendarGrid() {` and replace until `if (calendarTodayCount)`

start_str = "function renderCalendarGrid() {"
end_str = "    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;"

start_idx = js.find(start_str)
end_idx = js.find(end_str, start_idx) + len(end_str) + 1

if start_idx != -1 and end_idx != -1:
    new_render = """function renderCalendarGrid() {
    if (!calendarGridContent) return;

    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();

    const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    if (calendarMonthTitle) calendarMonthTitle.textContent = `${monthNames[month]} ${year}`;

    // Calculate days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    calendarGridContent.innerHTML = '';

    // Render Headers inside the same grid!
    const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    daysOfWeek.forEach(d => {
        const th = document.createElement('div');
        th.textContent = d;
        th.style.padding = '12px 8px';
        th.style.textAlign = 'center';
        th.style.fontSize = '12px';
        th.style.fontWeight = '600';
        th.style.color = 'var(--text-muted)';
        th.style.borderBottom = '1px solid var(--border)';
        th.style.borderRight = '1px solid var(--border)';
        th.style.textTransform = 'uppercase';
        calendarGridContent.appendChild(th);
    });

    const today = new Date();
    let todayCount = 0;

    // Previous month padding
    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--bg)';
        cell.style.borderRight = '1px solid var(--border)';
        cell.style.borderBottom = '1px solid var(--border)';
        cell.style.minHeight = '120px';
        calendarGridContent.appendChild(cell);
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

        const cell = document.createElement('div');
        cell.style.background = 'var(--surface)';
        cell.style.borderRight = '1px solid var(--border)';
        cell.style.borderBottom = '1px solid var(--border)';
        cell.style.minHeight = '120px';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';
        cell.style.transition = 'background 0.2s';
        
        cell.addEventListener('mouseover', () => { cell.style.background = 'var(--bg)'; });
        cell.addEventListener('mouseout', () => { cell.style.background = 'var(--surface)'; });

        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());

        // Day number
        const dayHeader = document.createElement('div');
        dayHeader.style.display = 'flex';
        dayHeader.style.justifyContent = 'center';
        dayHeader.style.marginBottom = '6px';
        
        const dayNumber = document.createElement('div');
        dayNumber.textContent = day;
        dayNumber.style.fontSize = '13px';
        dayNumber.style.width = '26px';
        dayNumber.style.height = '26px';
        dayNumber.style.display = 'flex';
        dayNumber.style.alignItems = 'center';
        dayNumber.style.justifyContent = 'center';
        dayNumber.style.borderRadius = '50%';
        dayNumber.style.fontWeight = isToday ? 'bold' : '500';
        
        if (isToday) {
            dayNumber.style.color = 'var(--primary)';
            dayNumber.style.background = 'rgba(139, 92, 246, 0.15)'; // Premium transparent mark
        } else {
            dayNumber.style.color = 'var(--text)';
        }
        
        dayHeader.appendChild(dayNumber);
        cell.appendChild(dayHeader);

        // Find appointments for this day
        const dayAppointments = globalAppointmentsList.filter(apt => {
            if (!apt.datetime_slot) return false;
            const d = new Date(apt.datetime_slot);
            return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
        });

        if (isToday) todayCount = dayAppointments.length;

        // Render appointments inside the cell
        dayAppointments.slice(0, 4).forEach(apt => {
            const aptEl = document.createElement('div');
            aptEl.style.background = apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)';
            aptEl.style.borderLeft = `3px solid ${apt.status === 'confirmada' ? '#10b981' : 'var(--primary)'}`;
            aptEl.style.padding = '3px 6px';
            aptEl.style.borderRadius = '0 4px 4px 0';
            aptEl.style.fontSize = '11px';
            aptEl.style.whiteSpace = 'nowrap';
            aptEl.style.overflow = 'hidden';
            aptEl.style.textOverflow = 'ellipsis';
            aptEl.style.color = 'var(--text)';
            
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente';
            
            aptEl.innerHTML = `<span style="font-weight: 600; opacity: 0.8;">${aptTime}</span> ${aptName}`;
            cell.appendChild(aptEl);
        });
        
        if (dayAppointments.length > 4) {
            const moreEl = document.createElement('div');
            moreEl.style.fontSize = '10px';
            moreEl.style.color = 'var(--text-muted)';
            moreEl.style.textAlign = 'center';
            moreEl.style.marginTop = '2px';
            moreEl.textContent = `+${dayAppointments.length - 4} más`;
            cell.appendChild(moreEl);
        }
        
        // Open Modal on click
        cell.addEventListener('click', () => {
            openCalendarModal(day, monthNames[month], year, dayAppointments);
        });

        calendarGridContent.appendChild(cell);
    }

    // Next month padding
    const totalCells = firstDay + daysInMonth;
    const remainingCells = (7 - (totalCells % 7)) % 7;
    for (let i = 0; i < remainingCells; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--bg)';
        cell.style.borderRight = '1px solid var(--border)';
        cell.style.borderBottom = '1px solid var(--border)';
        cell.style.minHeight = '120px';
        calendarGridContent.appendChild(cell);
    }

    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;
}

function openCalendarModal(day, monthStr, year, appointments) {
    const modal = document.getElementById('calendar-day-modal');
    const title = document.getElementById('calendar-day-modal-title');
    const content = document.getElementById('calendar-day-modal-content');
    
    if (!modal) return;
    
    title.textContent = `Citas: ${day} de ${monthStr} ${year}`;
    content.innerHTML = '';
    
    if (appointments.length === 0) {
        content.innerHTML = '<p style="color: var(--text-muted); text-align: center; margin: 20px 0;">No hay citas agendadas para este día.</p>';
    } else {
        appointments.forEach(apt => {
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente sin nombre';
            const statusColor = apt.status === 'confirmada' ? '#10b981' : 'var(--primary)';
            
            content.innerHTML += `
                <div style="background: var(--bg); border-left: 4px solid ${statusColor}; padding: 12px; margin-bottom: 12px; border-radius: 0 8px 8px 0; border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <strong style="color: var(--text);">${aptTime} - ${apt.service || 'Consulta'}</strong>
                        <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: ${apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)'}; color: ${statusColor}; text-transform: capitalize;">${apt.status}</span>
                    </div>
                    <div style="color: var(--text-muted); font-size: 13px;">${aptName} • Tel: ${apt.patient_phone || apt.chat_id || 'N/A'}</div>
                </div>
            `;
        });
    }
    
    modal.style.display = 'flex';
}
"""
    js = js[:start_idx] + new_render + js[end_idx:]

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
