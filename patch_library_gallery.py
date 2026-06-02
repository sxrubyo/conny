import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

new_library_html = """
            <!-- View: Library -->
            <section id="view-library" class="tab-view" style="padding: 0;">
                <div style="display: flex; flex-direction: column; height: 100vh; width: 100%;">
                    <div class="view-header" style="padding: 20px 24px; border-bottom: 1px solid var(--border); background: var(--bg);">
                        <h2 style="margin:0; font-size: 22px;">Biblioteca</h2>
                        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Sube recursos para que Conny los utilice. Control total sobre cada archivo.</p>
                        <!-- Hidden file input for native behavior -->
                        <input type="file" id="library-file-input" style="display: none;" multiple>
                    </div>
                    
                    <div class="library-container" style="flex: 1; padding: 24px; overflow-y: auto; background: var(--surface);">
                        <div id="library-resource-list" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; align-items: start;">
                            
                            <!-- Add Button (Big Square) -->
                            <div id="library-add-btn" style="aspect-ratio: 1 / 1; background: var(--bg); border: 2px dashed var(--border); border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s ease; color: var(--text-muted);" onmouseover="this.style.borderColor='var(--primary)'; this.style.color='var(--primary)';" onmouseout="this.style.borderColor='var(--border)'; this.style.color='var(--text-muted)';">
                                <div style="font-size: 48px; font-weight: 300; margin-bottom: 8px;">+</div>
                                <div style="font-size: 14px; font-weight: 500;">Añadir Recurso</div>
                            </div>
                            
                            <!-- Items injected by JS will go here -->
                        </div>
                    </div>
                </div>
            </section>
"""

html = re.sub(r'<!-- View: Library -->\s*<section id="view-library".*?</section>', new_library_html, html, flags=re.DOTALL)

# Bump version to avoid cache issues preventing JS execution
html = re.sub(r'src="/static/app\.js\?v=\d+"', 'src="/static/app.js?v=7"', html)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
