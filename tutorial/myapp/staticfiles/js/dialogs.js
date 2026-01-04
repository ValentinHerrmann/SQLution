// Shared helper to create and manage modal dialogs
function createModal(config) {
  return new Promise((resolve) => {
    // Clean up any stale modals
    document.querySelectorAll('.modal-overlay').forEach(m => m.remove());
    
    const modalId = config.modalId;
    const modalHtml = `
      <div id="${modalId}" class="modal-overlay" style="
          position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
          background: rgba(0,0,0,0.5); z-index: 9999; 
          display: flex; justify-content: center; align-items: center;">
          <div class="modal-content" style="
            background: white; padding: 20px; border-radius: 8px; 
            max-width: 400px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            background-color: var(--bg-tertiary); pointer-events: auto;">
            <div style="margin-bottom: 15px;">
              <i class="${config.iconClass}" style="font-size: 48px; color: ${config.color};"></i>
            </div>
            <p style="margin-bottom: 20px; font-size: 16px; color: var(--text-primary);">${config.message}</p>
            <div>
              ${config.buttons}
            </div>
          </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('.modal-content');
    let resolved = false;
    
    const safetyTimeout = setTimeout(() => {
      if (!resolved) closeModal(false);
    }, 60000);
    
    const closeModal = (result) => {
      if (resolved) return;
      resolved = true;
      clearTimeout(safetyTimeout);
      if (modal && modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
      resolve(result);
    };
    
    // Prevent clicks on modal content from bubbling
    if (modalContent) {
      modalContent.addEventListener('click', (e) => e.stopPropagation());
    }
    
    // Attach button handlers
    config.handlers.forEach(handler => {
      const btn = document.getElementById(handler.id);
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        closeModal(handler.result);
      });
    });
    
    // Handle clicking outside modal
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(false);
    });
  });
}

// Custom confirmation dialog with icon
function showConfirmDialog(message, iconClass = 'fas fa-exclamation-triangle', color = "var(--accent-warning)") {
  const timestamp = Date.now();
  const modalId = 'customConfirmModal_' + timestamp;
  const yesId = modalId + '_yes';
  const noId = modalId + '_no';
  
  return createModal({
    modalId: modalId,
    message: message,
    iconClass: iconClass,
    color: color,
    buttons: `
      <button id="${yesId}" class="btn btn-danger" style="margin-right: 10px; pointer-events: auto;">Weiter</button>
      <button id="${noId}" class="btn btn-primary" style="pointer-events: auto;">Abbrechen</button>
    `,
    handlers: [
      { id: yesId, result: true },
      { id: noId, result: false }
    ]
  });
}

function showAlertDialog(message, iconClass = 'fas fa-exclamation-triangle', color = "var(--accent-warning)") {
  const modalId = 'customAlertModal_' + Date.now();
  const okId = 'alertOk_' + Date.now();
  
  return createModal({
    modalId: modalId,
    message: message,
    iconClass: iconClass,
    color: color,
    buttons: `<button id="${okId}" class="btn btn-primary" style="margin-right: 10px; pointer-events: auto;">Ok</button>`,
    handlers: [
      { id: okId, result: true }
    ]
  });
}

// Make dialogs globally accessible
globalThis.showConfirmDialog = showConfirmDialog;
globalThis.showAlertDialog = showAlertDialog;