import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

pdf_logo = '<svg viewBox="0 0 24 24" width="48" height="48" fill="#ef4444"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>'
generic_logo = '<svg viewBox="0 0 24 24" width="48" height="48" fill="#8b5cf6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>'

start_str = "    if(libSaveBtn) libSaveBtn.addEventListener('click', () => {"
end_str = "        libraryAddBtn.insertAdjacentElement('afterend', card);\n        closeModal();\n    });"

start_idx = js.find(start_str)
end_idx = js.find(end_str) + len(end_str)

if start_idx != -1 and end_idx != -1:
    new_save_logic = """    if(libSaveBtn) libSaveBtn.addEventListener('click', () => {
        if (!pendingLibraryFile) return;
        
        const file = pendingLibraryFile;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        const instruction = libInstructions ? libInstructions.value.trim() : '';
        
        const card = document.createElement('div');
        card.className = 'resource-card gallery-item';
        card.style.background = 'var(--surface)';
        card.style.border = '1px solid var(--border)';
        card.style.borderRadius = '16px';
        card.style.overflow = 'hidden';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.aspectRatio = '1 / 1';
        card.style.animation = 'fadeIn 0.3s ease';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
        card.style.cursor = 'pointer';
        card.style.position = 'relative';
        
        let previewHtml = '';
        let modalPreviewHtml = '';
        if (file.type.startsWith('image/')) {
            const url = URL.createObjectURL(file);
            previewHtml = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;">`;
            modalPreviewHtml = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover;">`;
        } else if (file.name.toLowerCase().endsWith('.pdf')) {
            previewHtml = `<div style="width: 100%; height: 100%; background: rgba(239, 68, 68, 0.05); display: flex; align-items: center; justify-content: center; transition: background 0.3s ease;">` + `""" + pdf_logo + """` + `</div>`;
            modalPreviewHtml = previewHtml;
        } else {
            previewHtml = `<div style="width: 100%; height: 100%; background: rgba(139, 92, 246, 0.05); display: flex; align-items: center; justify-content: center; transition: background 0.3s ease;">` + `""" + generic_logo + """` + `</div>`;
            modalPreviewHtml = previewHtml;
        }
        
        card.innerHTML = `
            <div style="width: 100%; height: 100%; overflow: hidden;" class="preview-wrapper">
                ${previewHtml}
            </div>
            <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 12px; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); color: white; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;">
                <h4 style="margin: 0; font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 2px rgba(0,0,0,0.8);">${file.name}</h4>
            </div>
            <!-- Hover overlay -->
            <div class="hover-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(139,92,246,0.2); opacity: 0; transition: opacity 0.2s ease; display: flex; align-items: center; justify-content: center;">
                <div style="background: var(--surface); color: var(--text); padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">Ver detalles</div>
            </div>
        `;
        
        card.addEventListener('mouseover', () => {
            card.querySelector('.hover-overlay').style.opacity = '1';
            const img = card.querySelector('img');
            if(img) img.style.transform = 'scale(1.05)';
        });
        card.addEventListener('mouseout', () => {
            card.querySelector('.hover-overlay').style.opacity = '0';
            const img = card.querySelector('img');
            if(img) img.style.transform = 'scale(1)';
        });
        
        // Modal functionality
        card.addEventListener('click', () => {
            const detailModal = document.getElementById('library-detail-modal');
            if(!detailModal) return;
            
            document.getElementById('library-detail-preview').innerHTML = modalPreviewHtml;
            document.getElementById('library-detail-filename').textContent = file.name;
            document.getElementById('library-detail-filesize').textContent = sizeMb + ' MB';
            document.getElementById('library-detail-instructions').textContent = instruction ? '"' + instruction + '"' : '(Sin instrucciones especiales)';
            
            // Delete logic
            const delBtn = document.getElementById('library-detail-delete');
            // Remove old listeners by cloning
            const newDelBtn = delBtn.cloneNode(true);
            delBtn.parentNode.replaceChild(newDelBtn, delBtn);
            
            newDelBtn.addEventListener('click', () => {
                card.remove();
                detailModal.style.display = 'none';
            });
            
            detailModal.style.display = 'flex';
        });
        
        libraryAddBtn.insertAdjacentElement('afterend', card);
        closeModal();
    });
}

// Add close handler for detail modal
document.addEventListener('DOMContentLoaded', () => {
    const detailCloseBtn = document.getElementById('library-detail-close');
    const detailModal = document.getElementById('library-detail-modal');
    if (detailCloseBtn && detailModal) {
        detailCloseBtn.addEventListener('click', () => {
            detailModal.style.display = 'none';
        });
    }
});
"""
    js = js[:start_idx] + new_save_logic + js[end_idx:]
    with open("src/interfaces/web/static/app.js", "w") as f:
        f.write(js)
else:
    print("Could not find the JS block")
