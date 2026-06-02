import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Add navigation buttons
nav_buttons = """                <button class="nav-item" data-view="calendar" title="Calendario">
                    <svg class="nav-icon" viewBox="0 0 24 24"><path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2zm-7 5h5v5h-5z"/></svg>
                    <span class="nav-text">Calendario</span>
                </button>
                <button class="nav-item" data-view="library" title="Biblioteca">
                    <svg class="nav-icon" viewBox="0 0 24 24"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/></svg>
                    <span class="nav-text">Biblioteca</span>
                </button>"""

html = re.sub(r'(<button class="nav-item" data-view="admin-chat".*?</button>)',
              r'\1\n' + nav_buttons, html, flags=re.DOTALL)

# Add Views
new_views = """
            <!-- View: Calendar -->
            <section id="view-calendar" class="tab-view">
                <div class="view-header">
                    <h2>Calendario</h2>
                    <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Visualiza las citas agendadas por Conny en tiempo real.</p>
                </div>
                <div style="position: relative; margin-top: 20px;">
                    <!-- Floating button -->
                    <div style="position: absolute; top: -45px; right: 0; background: var(--primary); color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; box-shadow: 0 4px 12px rgba(139,92,246,0.3); z-index: 10;">
                        Hoy tienes <span id="calendar-today-count">3</span> citas
                    </div>
                    
                    <div class="calendar-container" style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                        <div class="calendar-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <button style="background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 6px 14px; border-radius: 6px; cursor: pointer;">&lt;</button>
                            <h3 style="margin: 0; font-size: 16px; color: var(--text);">Mayo 2026</h3>
                            <button style="background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 6px 14px; border-radius: 6px; cursor: pointer;">&gt;</button>
                        </div>
                        <div class="calendar-grid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; text-align: center;">
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Dom</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Lun</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Mar</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Mié</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Jue</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Vie</div>
                            <div style="color: var(--text-muted); font-size: 12px; padding-bottom: 8px;">Sáb</div>
                            
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.2s;">26</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.2s;">27</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.2s;">28</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.2s;">29</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; transition: all 0.2s;">30</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer; transition: all 0.2s;">1</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer; transition: all 0.2s;">2</div>
                            
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer; transition: all 0.2s;">3</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer; transition: all 0.2s;">4</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--primary); background: rgba(139,92,246,0.1); color: var(--text); cursor: pointer; position: relative;">5
                                <div style="width: 6px; height: 6px; background: var(--primary); border-radius: 50%; position: absolute; bottom: 4px; left: calc(50% - 3px);"></div>
                            </div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer;">6</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer;">7</div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--primary); background: rgba(139,92,246,0.1); color: var(--text); cursor: pointer; position: relative;">8
                                <div style="width: 6px; height: 6px; background: var(--primary); border-radius: 50%; position: absolute; bottom: 4px; left: calc(50% - 3px);"></div>
                            </div>
                            <div style="padding: 12px; border-radius: 8px; border: 1px solid var(--border); color: var(--text); cursor: pointer;">9</div>
                        </div>
                    </div>

                    <!-- Day Details -->
                    <div id="calendar-day-details" style="display: block; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;">
                        <h3 id="calendar-detail-title" style="margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 12px; color: var(--text); font-size: 16px;">Citas del 5 de Mayo (Confirmadas por Conny)</h3>
                        <div style="background: var(--bg); border-left: 4px solid var(--primary); padding: 14px; border-radius: 0 8px 8px 0; margin-bottom: 12px; border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);">
                            <div style="font-weight: 600; margin-bottom: 6px; color: var(--text); display: flex; justify-content: space-between;">
                                <span>10:00 AM - Consulta General</span>
                                <span style="font-size: 12px; background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 2px 8px; border-radius: 12px;">Confirmada</span>
                            </div>
                            <div style="color: var(--text-muted); font-size: 13px;">Cliente: Juan Pérez • Tel: +57 320 1234567</div>
                            <div style="color: var(--text-muted); font-size: 13px; margin-top: 4px; font-style: italic;">"Agendada automáticamente tras preguntar por los precios."</div>
                        </div>
                        <div style="background: var(--bg); border-left: 4px solid var(--primary); padding: 14px; border-radius: 0 8px 8px 0; border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);">
                            <div style="font-weight: 600; margin-bottom: 6px; color: var(--text); display: flex; justify-content: space-between;">
                                <span>02:30 PM - Valoración Estética</span>
                                <span style="font-size: 12px; background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 2px 8px; border-radius: 12px;">Confirmada</span>
                            </div>
                            <div style="color: var(--text-muted); font-size: 13px;">Cliente: María Gómez • Tel: +57 300 9876543</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- View: Library -->
            <section id="view-library" class="tab-view">
                <div class="view-header">
                    <h2>Biblioteca de Recursos</h2>
                    <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Sube imágenes, PDFs y links para que Conny los use y envíe en sus respuestas de WhatsApp.</p>
                </div>
                
                <div class="library-container" style="display: flex; gap: 24px; flex-wrap: wrap; margin-top: 24px;">
                    <!-- Upload Area -->
                    <div style="flex: 1; min-width: 280px; background: var(--surface); border: 1px dashed var(--border); border-radius: 12px; padding: 32px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: all 0.2s;">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 16px;">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        <h3 style="margin: 0 0 8px 0; color: var(--text); font-size: 16px;">Subir Nuevo Recurso</h3>
                        <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 24px;">Arrastra archivos aquí o haz clic para buscar en tu dispositivo.</p>
                        <button style="background: var(--primary); color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: 500; cursor: pointer; box-shadow: 0 2px 8px rgba(139,92,246,0.4);">Seleccionar Archivo</button>
                    </div>

                    <!-- Resource List -->
                    <div style="flex: 2; min-width: 320px; display: flex; flex-direction: column; gap: 16px;">
                        
                        <!-- Resource Item 1 -->
                        <div class="resource-card" style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;">
                            <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px;">
                                <div style="display: flex; align-items: center; gap: 16px;">
                                    <div style="background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 10px; color: #ef4444;">
                                        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0; font-size: 15px; color: var(--text);">Portafolio_Servicios_2026.pdf</h4>
                                        <span style="color: var(--text-muted); font-size: 12px;">Subido hace 2 días • 2.4 MB</span>
                                    </div>
                                </div>
                                <button style="background: transparent; border: none; color: var(--text-muted); cursor: pointer;"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg></button>
                            </div>
                            
                            <div style="background: var(--bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border);">
                                <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--text);">¿Cómo Conny debería usar este recurso?</label>
                                <select style="width: 100%; margin-bottom: 12px; padding: 10px; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; outline: none; font-size: 13px;">
                                    <option>Enviar cuando el cliente pregunte por precios generales o servicios</option>
                                    <option>Enviar al confirmar una cita médica (como preparación)</option>
                                    <option>Solo extraer información para responder (no enviar archivo)</option>
                                </select>
                                <textarea placeholder="Opcional: Instrucciones adicionales (Ej: 'Dile al cliente que aquí tiene los precios actualizados')..." style="width: 100%; height: 70px; padding: 10px; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; resize: none; font-family: inherit; font-size: 13px; outline: none; box-sizing: border-box;"></textarea>
                            </div>
                        </div>

                        <!-- Resource Item 2 -->
                        <div class="resource-card" style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;">
                            <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px;">
                                <div style="display: flex; align-items: center; gap: 16px;">
                                    <div style="background: rgba(59, 130, 246, 0.1); padding: 12px; border-radius: 10px; color: #3b82f6;">
                                        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0; font-size: 15px; color: var(--text);">Mapa_Ubicacion_Local.png</h4>
                                        <span style="color: var(--text-muted); font-size: 12px;">Subido hoy • 850 KB</span>
                                    </div>
                                </div>
                                <button style="background: transparent; border: none; color: var(--text-muted); cursor: pointer;"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg></button>
                            </div>
                            
                            <div style="background: var(--bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border);">
                                <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--text);">¿Cómo Conny debería usar este recurso?</label>
                                <select style="width: 100%; margin-bottom: 12px; padding: 10px; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; outline: none; font-size: 13px;">
                                    <option>Enviar si preguntan por la ubicación, dirección o cómo llegar</option>
                                    <option>Enviar junto con la confirmación de la reserva</option>
                                </select>
                                <textarea placeholder="Opcional: Instrucciones adicionales..." style="width: 100%; height: 50px; padding: 10px; background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; resize: none; font-family: inherit; font-size: 13px; outline: none; box-sizing: border-box;"></textarea>
                            </div>
                        </div>

                    </div>
                </div>
            </section>
"""

# Find where view-admin-chat ends
admin_chat_end = html.find('</section>\n\n            <!-- View: Consola Dev (Developer Admin Console) -->')
if admin_chat_end == -1:
    print("Could not find the end of view-admin-chat")
else:
    html = html[:admin_chat_end + 11] + new_views + html[admin_chat_end + 11:]

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)

print("index.html patched with new views and navigation")
