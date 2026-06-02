import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

# Replace view-dev-console with new dev views
dev_console_regex = r'<!-- View: Consola Dev \(Developer Admin Console\) -->.*?</section>'
new_views = """
            <!-- DEV VIEWS -->
            
            <!-- 1. Instancias -->
            <section id="view-dev-instances" class="tab-view active">
                <div class="view-header" style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); padding-bottom: 18px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #a78bfa; font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 10px;">
                            Instancias (PM2)
                        </h2>
                        <p style="color: var(--text-secondary); margin: 0; font-size: 13px;">Gestión y control del ciclo de vida de los procesos PM2 locales.</p>
                    </div>
                    <button type="button" id="btn-refresh-instances" class="btn" style="background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.35); padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 8px; cursor: pointer;">
                        Sincronizar
                    </button>
                </div>
                
                <div class="dev-panel" style="background: rgba(20, 16, 33, 0.45); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 20px;">
                    <div class="table-container" style="overflow-x: auto; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); background: rgba(10, 8, 20, 0.45);">
                        <table class="premium-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); background: rgba(139, 92, 246, 0.05);">
                                    <th style="padding: 12px 16px; font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase;">Nombre / Clínica</th>
                                    <th style="padding: 12px 16px; font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase;">Puerto</th>
                                    <th style="padding: 12px 16px; font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase;">Estado PM2</th>
                                    <th style="padding: 12px 16px; font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase;">Modelo Activo</th>
                                    <th style="padding: 12px 16px; font-size: 12px; font-weight: 600; color: #a78bfa; text-transform: uppercase; text-align: right;">Acciones</th>
                                </tr>
                            </thead>
                            <tbody id="dev-instances-tbody">
                                <!-- Inyectado dinámicamente -->
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Create New Instance -->
                <div class="dev-panel" style="background: rgba(20, 16, 33, 0.45); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 20px; margin-top: 20px;">
                    <h3 style="font-size: 16px; font-weight: 600; color: #f3f4f6; margin: 0 0 16px 0;">Nueva Instancia</h3>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <input type="text" id="new-instance-name" placeholder="Nombre (ej: clinicamedica)" style="flex: 1; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white;">
                        <button id="btn-create-instance" class="btn btn-primary" style="padding: 10px 20px; border-radius: 8px;">Desplegar Instancia</button>
                    </div>
                    <p id="new-instance-status-msg" style="margin: 10px 0 0 0; font-size: 13px;"></p>
                </div>
            </section>
            
            <!-- 2. Prompts -->
            <section id="view-dev-prompts" class="tab-view">
                <div class="view-header" style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); padding-bottom: 18px; margin-bottom: 24px;">
                    <h2 style="color: #a78bfa; font-weight: 700; margin-bottom: 4px;">Editor de Prompts</h2>
                    <p style="color: var(--text-secondary); margin: 0; font-size: 13px;">Edita el system prompt base de cada instancia en SQLite.</p>
                </div>
                <div class="dev-panel" style="background: rgba(20, 16, 33, 0.45); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; height: 70vh;">
                    <select id="dev-prompt-instance-select" style="padding: 10px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white; margin-bottom: 16px; outline: none;"></select>
                    <textarea id="dev-prompt-textarea" style="flex: 1; background: #0f0a1c; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 16px; color: #a78bfa; font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.5; outline: none; resize: none;" spellcheck="false" placeholder="Selecciona una instancia para cargar su prompt..."></textarea>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
                        <span id="prompt-status-msg" style="font-size: 13px; color: #34d399;"></span>
                        <button id="btn-save-prompt" class="btn btn-primary" style="border-radius: 8px; padding: 8px 24px;">Guardar Prompt</button>
                    </div>
                </div>
            </section>

            <!-- 3. Modelos -->
            <section id="view-dev-models" class="tab-view">
                <div class="view-header" style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); padding-bottom: 18px; margin-bottom: 24px;">
                    <h2 style="color: #a78bfa; font-weight: 700; margin-bottom: 4px;">Gestión de LLMs</h2>
                    <p style="color: var(--text-secondary); margin: 0; font-size: 13px;">Cambio de modelos de IA en caliente.</p>
                </div>
                <div class="dev-panel" style="background: rgba(20, 16, 33, 0.45); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 20px;">
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        <select id="dev-model-instance-select" style="padding: 10px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white;"></select>
                        <select id="dev-model-select" style="padding: 10px; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white;">
                            <option value="google/gemini-2.5-flash">Gemini 2.5 Flash</option>
                            <option value="google/gemini-2.5-pro">Gemini 2.5 Pro</option>
                            <option value="anthropic/claude-3-haiku">Claude 3.5 Haiku</option>
                            <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                        </select>
                        <button id="btn-apply-model" class="btn btn-primary" style="border-radius: 8px;">Aplicar Modelo y Reiniciar Instancia</button>
                    </div>
                </div>
            </section>

            <!-- 4. Accesos (Tokens & Admins) -->
            <section id="view-dev-tokens" class="tab-view">
                <div class="view-header" style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); padding-bottom: 18px; margin-bottom: 24px;">
                    <h2 style="color: #a78bfa; font-weight: 700; margin-bottom: 4px;">Tokens y Accesos</h2>
                    <p style="color: var(--text-secondary); margin: 0; font-size: 13px;">Gestión de Access Tokens para nuevos clientes.</p>
                </div>
                <div class="dev-panel" style="background: rgba(20, 16, 33, 0.45); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 16px; align-items: center;">
                        <h3 style="font-size: 16px; font-weight: 600; color: #f3f4f6; margin: 0;">Access Tokens Generados</h3>
                        <button id="btn-dev-create-token" class="btn btn-primary" style="padding: 8px 16px; border-radius: 8px; font-size: 13px;">+ Generar Token</button>
                    </div>
                    <div class="table-container" style="overflow-x: auto; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); background: rgba(10, 8, 20, 0.45);">
                        <table class="premium-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); background: rgba(139, 92, 246, 0.05);">
                                    <th style="padding: 12px 16px; font-size: 12px; color: #a78bfa; text-transform: uppercase;">Token</th>
                                    <th style="padding: 12px 16px; font-size: 12px; color: #a78bfa; text-transform: uppercase;">Clínica (Label)</th>
                                    <th style="padding: 12px 16px; font-size: 12px; color: #a78bfa; text-transform: uppercase;">Estado</th>
                                    <th style="padding: 12px 16px; font-size: 12px; color: #a78bfa; text-transform: uppercase; text-align: right;">Acción</th>
                                </tr>
                            </thead>
                            <tbody id="dev-tokens-tbody">
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- 5. Terminal -->
            <section id="view-dev-logs" class="tab-view">
                <div class="view-header" style="border-bottom: 1px solid rgba(139, 92, 246, 0.2); padding-bottom: 18px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="color: #a78bfa; font-weight: 700; margin-bottom: 4px;">Terminal Logs</h2>
                        <p style="color: var(--text-secondary); margin: 0; font-size: 13px;">Visor de logs en tiempo real (conny.log).</p>
                    </div>
                    <select id="dev-logs-instance-select" style="padding: 8px; border-radius: 6px; border: 1px solid rgba(139, 92, 246, 0.3); background: rgba(0,0,0,0.2); color: white;"></select>
                </div>
                <div class="dev-panel" style="background: #000; border: 1px solid #333; border-radius: 8px; padding: 16px; height: 65vh; overflow: hidden; position: relative;">
                    <div id="dev-terminal-logs" style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #a78bfa; line-height: 1.5; height: 100%; overflow-y: auto; white-space: pre-wrap; padding-bottom: 20px;">
                        Loading syslogs...
                    </div>
                </div>
            </section>

            <!-- END DEV VIEWS -->
"""
html = re.sub(dev_console_regex, new_views, html, flags=re.DOTALL)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)

