import re

with open("src/interfaces/web/static/index.html", "r") as f:
    html = f.read()

new_library_html = """
            <!-- View: Library -->
            <section id="view-library" class="tab-view" style="display: flex; flex-direction: column; height: 100vh; padding: 0;">
                <div class="view-header" style="padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg);">
                    <h2 style="margin:0; font-size: 22px;">Biblioteca</h2>
                    
                    <!-- Simple + Button -->
                    <button id="library-add-btn" title="Añadir Recurso" style="background: var(--primary); color: white; border: none; width: 40px; height: 40px; border-radius: 50%; font-size: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 12px rgba(139,92,246,0.3); transition: transform 0.2s;">
                        +
                    </button>
                    <!-- Hidden file input for native behavior -->
                    <input type="file" id="library-file-input" style="display: none;" multiple>
                </div>
                
                <div class="library-container" style="flex: 1; padding: 24px; overflow-y: auto; background: var(--surface);">
                    <div id="library-resource-list" style="display: flex; flex-direction: column; gap: 16px;">
                        <!-- Items injected by JS -->
                    </div>
                    
                    <div id="library-empty-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; color: var(--text-muted);">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom: 12px; opacity: 0.5;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="15" y2="15"></line><line x1="15" y1="9" x2="9" y2="15"></line></svg>
                        <p style="font-size: 14px; opacity: 0.8;">La biblioteca está vacía.</p>
                    </div>
                </div>
            </section>
"""

html = re.sub(r'<!-- View: Library -->\s*<section id="view-library".*?</section>', new_library_html, html, flags=re.DOTALL)

with open("src/interfaces/web/static/index.html", "w") as f:
    f.write(html)
