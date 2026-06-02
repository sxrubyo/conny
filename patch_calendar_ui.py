import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

new_calendar_html = """
            <!-- View: Calendar -->
            <section id="view-calendar" class="tab-view" style="display: flex; flex-direction: column; height: 100vh; padding: 0;">
                <div class="view-header" style="display: flex; justify-content: space-between; align-items: center; padding: 20px 24px 10px 24px; border-bottom: 1px solid var(--border);">
                    <div>
                        <h2 style="margin:0;">Calendario</h2>
                        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Visualiza las citas agendadas por Conny en tiempo real.</p>
                    </div>
                    <div style="background: var(--primary); color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; box-shadow: 0 4px 12px rgba(139,92,246,0.3);">
                        Hoy tienes <span id="calendar-today-count">0</span> citas
                    </div>
                </div>
                
                <div class="calendar-container" style="flex: 1; display: flex; flex-direction: column; background: var(--bg); padding: 16px; overflow: hidden;">
                    <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <button id="calendar-prev-btn" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">&lt; Mes Anterior</button>
                        <h3 id="calendar-month-title" style="margin: 0; font-size: 20px; color: var(--text);">Mayo 2026</h3>
                        <button id="calendar-next-btn" style="background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">Mes Siguiente &gt;</button>
                    </div>
                    
                    <!-- Days Header -->
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: var(--border); border: 1px solid var(--border); border-top-left-radius: 8px; border-top-right-radius: 8px;">
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center; border-top-left-radius: 8px;">Dom</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center;">Lun</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center;">Mar</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center;">Mié</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center;">Jue</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center;">Vie</div>
                        <div style="background: var(--surface); color: var(--text-muted); font-size: 13px; font-weight: bold; padding: 12px; text-align: center; border-top-right-radius: 8px;">Sáb</div>
                    </div>
                    
                    <!-- Calendar Grid -->
                    <div id="calendar-grid-content" style="display: grid; grid-template-columns: repeat(7, 1fr); grid-auto-rows: minmax(120px, 1fr); gap: 1px; background: var(--border); border-left: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; flex: 1; overflow-y: auto;">
                        <!-- Injected by JS -->
                    </div>
                </div>
            </section>
"""

html = re.sub(r'<!-- View: Calendar -->\s*<section id="view-calendar".*?</section>', new_calendar_html, html, flags=re.DOTALL)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
