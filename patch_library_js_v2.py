import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

start_idx = js.find("// ── Library View Logic ──")
if start_idx != -1:
    js = js[:start_idx]

# A proper PDF base64 logo (small placeholder)
pdf_logo = '<svg viewBox="0 0 24 24" width="48" height="48" fill="#ef4444"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>'
generic_logo = '<svg viewBox="0 0 24 24" width="48" height="48" fill="#8b5cf6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>'

new_library_logic = """
// ── Library View Logic ──
const libraryAddBtn = document.getElementById('library-add-btn');
const libraryFileInput = document.getElementById('library-file-input');
const libraryResourceList = document.getElementById('library-resource-list');

// Modal Elements
const libModal = document.getElementById('library-config-modal');
const libCloseBtn = document.getElementById('library-config-close');
const libCancelBtn = document.getElementById('library-config-cancel');
const libSaveBtn = document.getElementById('library-config-save');
const libPreviewContainer = document.getElementById('library-preview-container');
const libFilename = document.getElementById('library-config-filename');
const libFilesize = document.getElementById('library-config-filesize');
const libInstructions = document.getElementById('library-config-instructions');

let pendingLibraryFile = null;
let pendingLibraryPreviewUrl = null;

if (libraryAddBtn && libraryFileInput) {
    libraryAddBtn.addEventListener('click', () => {
        libraryFileInput.click();
    });

    libraryFileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            const file = files[0];
            pendingLibraryFile = file;
            const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
            
            libFilename.textContent = file.name;
            libFilesize.textContent = sizeMb + " MB";
            libInstructions.value = "";
            
            // Generate Preview
            libPreviewContainer.innerHTML = '';
            libPreviewContainer.style.background = 'var(--bg)';
            if (pendingLibraryPreviewUrl) {
                URL.revokeObjectURL(pendingLibraryPreviewUrl);
                pendingLibraryPreviewUrl = null;
            }
            
            if (file.type.startsWith('image/')) {
                pendingLibraryPreviewUrl = URL.createObjectURL(file);
                libPreviewContainer.innerHTML = `<img src="${pendingLibraryPreviewUrl}" style="width: 100%; height: 100%; object-fit: cover;">`;
            } else if (file.name.toLowerCase().endsWith('.pdf')) {
                libPreviewContainer.innerHTML = `""" + pdf_logo + """`;
                libPreviewContainer.style.background = 'rgba(239, 68, 68, 0.05)';
            } else {
                libPreviewContainer.innerHTML = `""" + generic_logo + """`;
                libPreviewContainer.style.background = 'rgba(139, 92, 246, 0.05)';
            }
            
            libModal.style.display = 'flex';
        }
    });
    
    const closeModal = () => {
        libModal.style.display = 'none';
        libraryFileInput.value = '';
        pendingLibraryFile = null;
    };
    
    libCloseBtn.addEventListener('click', closeModal);
    libCancelBtn.addEventListener('click', closeModal);
    
    libSaveBtn.addEventListener('click', () => {
        if (!pendingLibraryFile) return;
        
        const file = pendingLibraryFile;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        const instruction = libInstructions.value.trim();
        
        const card = document.createElement('div');
        card.className = 'resource-card gallery-item';
        card.style.background = 'var(--bg)';
        card.style.border = '1px solid var(--border)';
        card.style.borderRadius = '16px';
        card.style.overflow = 'hidden';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.height = '100%';
        card.style.animation = 'fadeIn 0.3s ease';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
        
        let previewHtml = '';
        if (file.type.startsWith('image/')) {
            const url = URL.createObjectURL(file);
            previewHtml = `<img src="${url}" style="width: 100%; height: 140px; object-fit: cover; border-bottom: 1px solid var(--border);">`;
        } else if (file.name.toLowerCase().endsWith('.pdf')) {
            previewHtml = `<div style="height: 140px; background: rgba(239, 68, 68, 0.05); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: center;">` + `""" + pdf_logo + """` + `</div>`;
        } else {
            previewHtml = `<div style="height: 140px; background: rgba(139, 92, 246, 0.05); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: center;">` + `""" + generic_logo + """` + `</div>`;
        }
        
        card.innerHTML = `
            ${previewHtml}
            <div style="padding: 16px; display: flex; flex-direction: column; flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <h4 style="margin: 0; font-size: 14px; color: var(--text); word-break: break-all; line-height: 1.3;">${file.name}</h4>
                    <button class="lib-del-btn" title="Eliminar" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 0 0 0 8px; transition: color 0.2s;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='var(--text-muted)'">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
                <span style="color: var(--text-muted); font-size: 12px; margin-bottom: 16px;">${sizeMb} MB</span>
                
                ${instruction ? `
                <div style="margin-top: auto; padding: 10px 12px; background: var(--surface); border-radius: 8px; border: 1px solid var(--border);">
                    <div style="font-size: 11px; font-weight: 600; color: var(--primary); margin-bottom: 4px; text-transform: uppercase;">Control:</div>
                    <div style="font-size: 12px; color: var(--text); font-style: italic;">"${instruction}"</div>
                </div>
                ` : `
                <div style="margin-top: auto; font-size: 12px; color: var(--text-muted); font-style: italic; padding: 10px 0;">(Sin instrucciones)</div>
                `}
            </div>
        `;
        
        card.querySelector('.lib-del-btn').addEventListener('click', () => {
            card.remove();
        });
        
        libraryAddBtn.insertAdjacentElement('afterend', card);
        closeModal();
    });
}
"""

js = js + new_library_logic

with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
