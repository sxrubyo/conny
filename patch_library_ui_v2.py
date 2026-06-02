import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

library_modal = """
    <!-- Modal para Biblioteca (Configurar Recurso) -->
    <div id="library-config-modal" class="modal" style="display: none; align-items: center; justify-content: center; background: rgba(0,0,0,0.6); z-index: 1000; backdrop-filter: blur(2px);">
        <div style="background: var(--surface); border-radius: 16px; width: 450px; max-width: 90%; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden;">
            <div style="padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg);">
                <h3 style="margin: 0; font-size: 16px; color: var(--text);">Configurar Recurso</h3>
                <button id="library-config-close" style="background: transparent; border: none; font-size: 24px; color: var(--text-muted); cursor: pointer; line-height: 1;">&times;</button>
            </div>
            <div style="padding: 24px;">
                <div style="display: flex; gap: 16px; margin-bottom: 24px;">
                    <div id="library-preview-container" style="width: 80px; height: 80px; border-radius: 8px; background: var(--bg); display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid var(--border);">
                        <!-- Preview injected by JS -->
                    </div>
                    <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                        <div id="library-config-filename" style="font-weight: 600; color: var(--text); font-size: 15px; word-break: break-all; margin-bottom: 4px;"></div>
                        <div id="library-config-filesize" style="color: var(--text-muted); font-size: 13px;"></div>
                    </div>
                </div>
                
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 8px;">Control de Conny</label>
                    <input type="text" id="library-config-instructions" placeholder="Ej: Envía esto si te preguntan por la ubicación" style="width: 100%; padding: 12px 16px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; font-size: 14px; outline: none; transition: border-color 0.2s;" onfocus="this.style.borderColor='var(--primary)'" onblur="this.style.borderColor='var(--border)'">
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 12px;">
                    <button id="library-config-cancel" style="background: transparent; color: var(--text-muted); border: 1px solid var(--border); padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;">Cancelar</button>
                    <button id="library-config-save" style="background: var(--primary); color: white; border: none; padding: 10px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; box-shadow: 0 4px 12px rgba(139,92,246,0.3);">Guardar en Biblioteca</button>
                </div>
            </div>
        </div>
    </div>
"""

html = html.replace('<!-- Modal de Configuración -->', library_modal + '\n    <!-- Modal de Configuración -->')

# Update JS version
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=9"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
