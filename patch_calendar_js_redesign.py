import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

start_str = "function renderCalendarGrid() {"
end_str = "    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;\n}"

start_idx = js.find(start_str)
end_idx = js.find(end_str, start_idx) + len(end_str)

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

    // Render Headers inside the grid
    const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    daysOfWeek.forEach(d => {
        const th = document.createElement('div');
        th.textContent = d;
        th.style.padding = '4px 12px 12px 12px';
        th.style.textAlign = 'right';
        th.style.fontSize = '12px';
        th.style.fontWeight = '600';
        th.style.color = 'var(--text-muted)';
        th.style.textTransform = 'uppercase';
        calendarGridContent.appendChild(th);
    });

    const today = new Date();
    let todayCount = 0;

    // Previous month padding
    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'transparent';
        cell.style.minHeight = '120px';
        calendarGridContent.appendChild(cell);
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

        const cell = document.createElement('div');
        cell.style.background = 'var(--surface)';
        cell.style.border = '1px solid var(--border)';
        cell.style.borderRadius = '12px';
        cell.style.minHeight = '120px';
        cell.style.padding = '10px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '6px';
        cell.style.cursor = 'pointer';
        cell.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)';

        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());

        // Day number
        const dayHeader = document.createElement('div');
        dayHeader.style.display = 'flex';
        dayHeader.style.justifyContent = 'flex-end';
        dayHeader.style.marginBottom = '6px';
        
        const dayNumber = document.createElement('div');
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
            dayNumber.style.color = 'var(--primary)';
            dayNumber.style.background = 'rgba(139, 92, 246, 0.15)';
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
        dayAppointments.slice(0, 3).forEach(apt => {
            const aptEl = document.createElement('div');
            aptEl.style.background = apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)';
            aptEl.style.borderLeft = `3px solid ${apt.status === 'confirmada' ? '#10b981' : 'var(--primary)'}`;
            aptEl.style.padding = '4px 8px';
            aptEl.style.borderRadius = '0 4px 4px 0';
            aptEl.style.fontSize = '11px';
            aptEl.style.whiteSpace = 'nowrap';
            aptEl.style.overflow = 'hidden';
            aptEl.style.textOverflow = 'ellipsis';
            aptEl.style.color = 'var(--text)';
            
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente';
            
            aptEl.innerHTML = `<span style="font-weight: 600;">${aptTime}</span> <span style="opacity:0.8; margin-left:4px;">${aptName}</span>`;
            cell.appendChild(aptEl);
        });
        
        if (dayAppointments.length > 3) {
            const moreEl = document.createElement('div');
            moreEl.style.fontSize = '11px';
            moreEl.style.color = 'var(--text-muted)';
            moreEl.style.fontWeight = '600';
            moreEl.style.marginTop = '4px';
            moreEl.textContent = `+${dayAppointments.length - 3} más`;
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
        cell.style.background = 'transparent';
        cell.style.minHeight = '120px';
        calendarGridContent.appendChild(cell);
    }

    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;
}"""

    # We also need to fix openCalendarModal so it matches the new empty state design
    start_modal = "function openCalendarModal(day, monthStr, year, appointments) {"
    end_modal = "    modal.style.display = 'flex';\n}"
    m_start = js.find(start_modal, end_idx)
    m_end = js.find(end_modal, m_start) + len(end_modal)
    
    new_modal = """function openCalendarModal(day, monthStr, year, appointments) {
    const modal = document.getElementById('calendar-day-modal');
    const title = document.getElementById('calendar-day-modal-title');
    const content = document.getElementById('calendar-day-modal-content');

    if (!modal) return;

    title.textContent = `${day} de ${monthStr} ${year}`;
    content.innerHTML = '';

    if (appointments.length === 0) {
        content.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 0; opacity: 0.6;">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-muted)" stroke-width="1.5" style="margin-bottom: 16px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <p style="color: var(--text-muted); font-size: 15px; font-weight: 500; margin: 0;">Día libre</p>
                <p style="color: var(--text-muted); font-size: 13px; margin: 4px 0 0 0;">No hay citas agendadas para este día.</p>
            </div>
        `;
    } else {
        appointments.forEach(apt => {
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente sin nombre';
            const statusColor = apt.status === 'confirmada' ? '#10b981' : 'var(--primary)';

            content.innerHTML += `
                <div style="background: var(--bg); border-left: 4px solid ${statusColor}; padding: 16px; margin-bottom: 16px; border-radius: 0 12px 12px 0; border: 1px solid var(--border); border-left-width: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="color: var(--text); font-size: 15px;">${aptTime} - ${apt.service || 'Consulta'}</strong>
                        <span style="font-size: 11px; padding: 4px 10px; border-radius: 12px; font-weight: 600; background: ${apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)'}; color: ${statusColor}; text-transform: capitalize;">${apt.status}</span>
                    </div>
                    <div style="color: var(--text-muted); font-size: 14px; font-weight: 500;">${aptName}</div>
                    <div style="color: var(--text-muted); font-size: 13px; margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                        ${apt.patient_phone || apt.chat_id || 'N/A'}
                    </div>
                </div>
            `;
        });
    }

    modal.style.display = 'flex';
}"""

    js = js[:start_idx] + new_render + js[end_idx:m_start] + new_modal + js[m_end:]
    with open("src/interfaces/web/static/app.js", "w") as f:
        f.write(js)
