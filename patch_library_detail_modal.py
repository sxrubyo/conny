import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

library_detail_modal = """
    <!-- Modal para Detalles de Recurso -->
    <div id="library-detail-modal" class="modal" style="display: none; align-items: center; justify-content: center; background: rgba(0,0,0,0.6); z-index: 1000; backdrop-filter: blur(2px);">
        <div style="background: var(--surface); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden;">
            <div style="padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg);">
                <h3 style="margin: 0; font-size: 16px; color: var(--text);">Detalles del Recurso</h3>
                <button id="library-detail-close" style="background: transparent; border: none; font-size: 24px; color: var(--text-muted); cursor: pointer; line-height: 1;">&times;</button>
            </div>
            <div style="padding: 24px;">
                <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 24px;">
                    <div id="library-detail-preview" style="width: 120px; height: 120px; border-radius: 12px; background: var(--bg); display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid var(--border); margin-bottom: 16px;">
                        <!-- Preview injected by JS -->
                    </div>
                    <div id="library-detail-filename" style="font-weight: 600; color: var(--text); font-size: 15px; word-break: break-all; text-align: center; margin-bottom: 4px;"></div>
                    <div id="library-detail-filesize" style="color: var(--text-muted); font-size: 13px;"></div>
                </div>
                
                <div style="background: var(--bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 24px;">
                    <div style="font-size: 11px; font-weight: 600; color: var(--primary); margin-bottom: 8px; text-transform: uppercase;">Instrucciones para Conny:</div>
                    <div id="library-detail-instructions" style="font-size: 14px; color: var(--text); font-style: italic;"></div>
                </div>
                
                <div style="display: flex; justify-content: flex-end;">
                    <button id="library-detail-delete" style="background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500; transition: all 0.2s;" onmouseover="this.style.background='#ef4444'; this.style.color='white';" onmouseout="this.style.background='rgba(239, 68, 68, 0.1)'; this.style.color='#ef4444';">Eliminar Recurso</button>
                </div>
            </div>
        </div>
    </div>
"""

# Insert it before the config modal or settings modal
html = html.replace('<!-- Modal para Biblioteca (Configurar Recurso) -->', library_detail_modal + '\n    <!-- Modal para Biblioteca (Configurar Recurso) -->')

# Bump version to 10
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=10"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
