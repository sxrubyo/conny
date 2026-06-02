import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Replace calendar header and grid container
new_calendar_html = """
                <div class="calendar-container" style="flex: 1; display: flex; flex-direction: column; background: var(--bg); padding: 24px; overflow: hidden;">
                    <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                        
                        <!-- Today Badge -->
                        <div style="background: var(--surface); color: var(--text); padding: 10px 20px; border-radius: 8px; border: 1px solid var(--border); font-weight: 600; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            Hoy tienes <span id="calendar-today-count" style="color: var(--primary); font-size: 16px;">0</span> citas
                        </div>
                        
                        <!-- Month Nav -->
                        <div style="display: flex; align-items: center; gap: 16px; margin-right: 8px;">
                            <button id="calendar-prev-btn" title="Mes Anterior" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); width: 40px; height: 40px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">&lt;</button>
                            <h3 id="calendar-month-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text); min-width: 150px; text-align: center; text-transform: capitalize;">Mayo 2026</h3>
                            <button id="calendar-next-btn" title="Mes Siguiente" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); width: 40px; height: 40px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">&gt;</button>
                        </div>
                    </div>
                    
                    <div style="flex: 1; overflow-y: auto;">
                        <div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; min-width: 800px; padding-bottom: 20px;">
                            <!-- Header and cells injected by JS so alignment is perfect -->
                        </div>
                    </div>
                </div>
"""

html = re.sub(r'<div class="calendar-container".*?(</section>)', new_calendar_html + '\n            \\1', html, flags=re.DOTALL)

# Let's fix the modal so it closes when clicking outside and looks better
new_modal_html = """
    <!-- Modal para citas del día -->
    <div id="calendar-day-modal" class="modal" style="display: none; align-items: center; justify-content: center; background: rgba(0,0,0,0.4); z-index: 1000;" onclick="if(event.target === this) this.style.display='none';">
        <div style="background: var(--surface); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; display: flex; flex-direction: column;">
            <div style="padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg);">
                <h3 id="calendar-day-modal-title" style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text);">Citas Programadas</h3>
                <button onclick="document.getElementById('calendar-day-modal').style.display='none'" style="background: var(--surface); border: 1px solid var(--border); border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: var(--text-muted); cursor: pointer;">&times;</button>
            </div>
            <div id="calendar-day-modal-content" style="padding: 24px; max-height: 60vh; overflow-y: auto; background: var(--surface);">
                <!-- Appointments here -->
            </div>
        </div>
    </div>
"""

html = re.sub(r'<!-- Modal para citas del día -->.*?</div>\s*</div>\s*</div>', new_modal_html, html, flags=re.DOTALL)

html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=11"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
