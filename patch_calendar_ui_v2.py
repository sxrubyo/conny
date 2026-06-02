import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Replace the whole calendar container logic
new_calendar_html = """
                <div class="calendar-container" style="flex: 1; display: flex; flex-direction: column; background: var(--surface); padding: 24px; overflow: hidden;">
                    <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                        <h3 id="calendar-month-title" style="margin: 0; font-size: 24px; font-weight: 400; color: var(--text);">Mayo 2026</h3>
                        <div style="display: flex; gap: 8px;">
                            <button id="calendar-prev-btn" title="Mes Anterior" style="background: transparent; border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px;">&lt;</button>
                            <button id="calendar-next-btn" title="Mes Siguiente" style="background: transparent; border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px;">&gt;</button>
                        </div>
                    </div>
                    
                    <div style="flex: 1; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; background: var(--bg);">
                        <div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); min-width: 800px;">
                            <!-- Header and cells injected by JS so alignment is perfect -->
                        </div>
                    </div>
                </div>
"""

html = re.sub(r'<div class="calendar-container".*?(</section>)', new_calendar_html + '\n            \\1', html, flags=re.DOTALL)

# Inject Calendar Modal for Day Click
calendar_modal = """
    <!-- Modal para citas del día -->
    <div id="calendar-day-modal" class="modal" style="display: none; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); z-index: 1000;">
        <div style="background: var(--surface); border-radius: 12px; width: 400px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.2); overflow: hidden;">
            <div style="padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg);">
                <h3 id="calendar-day-modal-title" style="margin: 0; font-size: 16px; color: var(--text);">Citas</h3>
                <button onclick="document.getElementById('calendar-day-modal').style.display='none'" style="background: transparent; border: none; font-size: 20px; color: var(--text-muted); cursor: pointer;">&times;</button>
            </div>
            <div id="calendar-day-modal-content" style="padding: 20px; max-height: 60vh; overflow-y: auto;">
                <!-- Appointments here -->
            </div>
        </div>
    </div>
"""

# Place it before the Settings Modal
html = html.replace('<!-- Modal de Configuración -->', calendar_modal + '\n    <!-- Modal de Configuración -->')

# Update JS version
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=8"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
