import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

library_logic = """
// ── Library View Logic ──
const libraryAddBtn = document.getElementById('library-add-btn');
const libraryFileInput = document.getElementById('library-file-input');
const libraryResourceList = document.getElementById('library-resource-list');
const libraryEmptyState = document.getElementById('library-empty-state');

if (libraryAddBtn && libraryFileInput) {
    libraryAddBtn.addEventListener('click', () => {
        libraryFileInput.click();
    });

    libraryFileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            libraryEmptyState.style.display = 'none';
        }
        
        files.forEach(file => {
            const isPdf = file.name.toLowerCase().endsWith('.pdf');
            
            // Icon SVG based on file type
            const iconSvg = isPdf 
                ? '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
                : '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>';
            
            const iconColor = isPdf ? '#ef4444' : '#3b82f6';
            const iconBg = isPdf ? 'rgba(239, 68, 68, 0.1)' : 'rgba(59, 130, 246, 0.1)';
            
            const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
            
            const card = document.createElement('div');
            card.className = 'resource-card';
            card.style.background = 'var(--bg)';
            card.style.border = '1px solid var(--border)';
            card.style.borderRadius = '12px';
            card.style.padding = '20px';
            card.style.animation = 'fadeIn 0.3s ease';
            
            card.innerHTML = `
                <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="background: ${iconBg}; padding: 12px; border-radius: 10px; color: ${iconColor};">
                            ${iconSvg}
                        </div>
                        <div>
                            <h4 style="margin: 0; font-size: 15px; color: var(--text);">${file.name}</h4>
                            <span style="color: var(--text-muted); font-size: 12px;">Recién subido • ${sizeMb} MB</span>
                        </div>
                    </div>
                    <button class="lib-del-btn" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 4px;">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
                
                <div style="background: var(--surface); padding: 16px; border-radius: 8px; border: 1px solid var(--border);">
                    <label style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--text);">Instrucciones (Control Total)</label>
                    <textarea placeholder="Ej: Usa este documento cuando te pidan la lista de precios..." style="width: 100%; height: 70px; padding: 10px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; resize: none; font-family: inherit; font-size: 13px; outline: none; box-sizing: border-box;"></textarea>
                    <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                        <button style="background: var(--primary); color: white; border: none; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500;">Guardar Instrucción</button>
                    </div>
                </div>
            `;
            
            card.querySelector('.lib-del-btn').addEventListener('click', () => {
                card.remove();
                if (libraryResourceList.children.length === 0) {
                    libraryEmptyState.style.display = 'flex';
                }
            });
            
            card.querySelector('button:last-child').addEventListener('click', function() {
                const btn = this;
                btn.textContent = 'Guardado ✓';
                btn.style.background = '#10b981';
                setTimeout(() => {
                    btn.textContent = 'Guardar Instrucción';
                    btn.style.background = 'var(--primary)';
                }, 2000);
            });
            
            libraryResourceList.prepend(card);
        });
        
        // Reset file input
        libraryFileInput.value = '';
    });
}
"""

js = js + "\n" + library_logic

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
