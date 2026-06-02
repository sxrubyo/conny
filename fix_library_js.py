import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# I will completely replace the previous library logic block.
# Since it might be hard to regex the exact block, I'll just look for "// ── Library View Logic ──" to the end of file.

start_idx = js.find("// ── Library View Logic ──")
if start_idx != -1:
    js = js[:start_idx]

new_library_logic = """
// ── Library View Logic ──
const libraryAddBtn = document.getElementById('library-add-btn');
const libraryFileInput = document.getElementById('library-file-input');
const libraryResourceList = document.getElementById('library-resource-list');

if (libraryAddBtn && libraryFileInput) {
    libraryAddBtn.addEventListener('click', () => {
        libraryFileInput.click();
    });

    libraryFileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        
        files.forEach(file => {
            const isPdf = file.name.toLowerCase().endsWith('.pdf');
            const isImg = file.type.startsWith('image/');
            
            // Icon SVG based on file type
            const iconSvg = isImg 
                ? '<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>'
                : isPdf 
                ? '<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>'
                : '<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>';
            
            const iconColor = isImg ? '#3b82f6' : (isPdf ? '#ef4444' : '#8b5cf6');
            const iconBg = isImg ? 'rgba(59, 130, 246, 0.1)' : (isPdf ? 'rgba(239, 68, 68, 0.1)' : 'rgba(139, 92, 246, 0.1)');
            
            const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
            
            const card = document.createElement('div');
            card.className = 'resource-card gallery-item';
            card.style.background = 'var(--bg)';
            card.style.border = '1px solid var(--border)';
            card.style.borderRadius = '16px';
            card.style.padding = '20px';
            card.style.display = 'flex';
            card.style.flexDirection = 'column';
            card.style.height = '100%';
            card.style.animation = 'fadeIn 0.3s ease';
            card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
            
            card.innerHTML = `
                <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px;">
                    <div style="background: ${iconBg}; padding: 16px; border-radius: 12px; color: ${iconColor}; display: flex; align-items: center; justify-content: center; aspect-ratio: 1/1; width: 64px;">
                        ${iconSvg}
                    </div>
                    <button class="lib-del-btn" title="Eliminar" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 4px; transition: color 0.2s;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='var(--text-muted)'">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
                
                <h4 style="margin: 0 0 4px 0; font-size: 15px; color: var(--text); word-break: break-all; line-height: 1.3;">${file.name}</h4>
                <span style="color: var(--text-muted); font-size: 12px; margin-bottom: 16px; display: block;">${sizeMb} MB</span>
                
                <div style="background: var(--surface); padding: 14px; border-radius: 12px; border: 1px solid var(--border); margin-top: auto;">
                    <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 8px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Control de Conny</label>
                    <textarea placeholder="Ej: Envía esta imagen cuando el cliente pregunte por la ubicación..." style="width: 100%; height: 60px; padding: 10px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; resize: none; font-family: inherit; font-size: 13px; outline: none; box-sizing: border-box; transition: border-color 0.2s;" onfocus="this.style.borderColor='var(--primary)'" onblur="this.style.borderColor='var(--border)'"></textarea>
                    <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                        <button class="save-instruction-btn" style="background: var(--bg); color: var(--primary); border: 1px solid var(--primary); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;">Guardar</button>
                    </div>
                </div>
            `;
            
            card.querySelector('.lib-del-btn').addEventListener('click', () => {
                card.remove();
            });
            
            card.querySelector('.save-instruction-btn').addEventListener('click', function() {
                const btn = this;
                btn.textContent = '¡Guardado!';
                btn.style.background = 'var(--primary)';
                btn.style.color = 'white';
                setTimeout(() => {
                    btn.textContent = 'Guardar';
                    btn.style.background = 'var(--bg)';
                    btn.style.color = 'var(--primary)';
                }, 2000);
            });
            
            // Insert AFTER the add button
            libraryAddBtn.insertAdjacentElement('afterend', card);
        });
        
        // Reset file input
        libraryFileInput.value = '';
    });
}
"""

js = js + new_library_logic

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
