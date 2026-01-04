// Custom confirmation dialog with icon
function showConfirmDialog(message, iconClass = 'fas fa-exclamation-triangle', color="var(--accent-warning)") {
  return new Promise((resolve) => {
    // Clean up any stale modals first
    const staleModals = document.querySelectorAll('.modal-overlay');
    staleModals.forEach(m => m.remove());
    
    // Use unique ID to avoid conflicts
    const timestamp = Date.now();
    const modalId = 'customConfirmModal_' + timestamp;
    const yesId = modalId + '_yes';
    const noId = modalId + '_no';
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
              <i class="${iconClass}" style="font-size: 48px; color: ${color};"></i>
            </div>
            <p style="margin-bottom: 20px; font-size: 16px; color: var(--text-primary);">${message}</p>
            <div>
              <button id="${yesId}" class="btn btn-danger" style="margin-right: 10px; pointer-events: auto;">Weiter</button>
              <button id="${noId}" class="btn btn-primary" style="pointer-events: auto;">Abbrechen</button>
            </div>
          </div>
        </div>
    `;
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = document.getElementById(modalId);
    const yesBtn = document.getElementById(yesId);
    const noBtn = document.getElementById(noId);
    const modalContent = modal.querySelector('.modal-content');
    let resolved = false;
    let resolveFn = resolve;
    
    // Safety timeout - auto-close after 60 seconds
    const safetyTimeout = setTimeout(() => {
      if (!resolved) {
        closeModal(false);
      }
    }, 60000);
    
    // Helper to close modal
    const closeModal = (result) => {
      if (resolved) return;
      resolved = true;
      
      // Clear the safety timeout
      clearTimeout(safetyTimeout);
      
      // Remove the modal immediately
      if (modal && modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
      
      // Resolve the promise
      resolveFn(result);
    };
    
    // Stop propagation on modal content
    if (modalContent) {
      modalContent.addEventListener('click', (e) => {
        e.stopPropagation();
      });
    }
    
    // Handle yes button
    yesBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeModal(true);
    });
    
    // Handle no button
    noBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeModal(false);
    });
    
    // Handle clicking outside modal
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(false);
      }
    });
  });
}

function showAlertDialog(message, iconClass = 'fas fa-exclamation-triangle', color="var(--accent-warning)") {
  return new Promise((resolve) => {
    // Clean up any stale modals first
    const staleModals = document.querySelectorAll('.modal-overlay');
    staleModals.forEach(m => m.remove());
    
    // Use unique ID to avoid conflicts
    const modalId = 'customAlertModal_' + Date.now();
    const okId = 'alertOk_' + Date.now();
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
              <i class="${iconClass}" style="font-size: 48px; color: ${color};"></i>
            </div>
            <p style="margin-bottom: 20px; font-size: 16px; color: var(--text-primary);">${message}</p>
            <div>
              <button id="${okId}" class="btn btn-primary" style="margin-right: 10px; pointer-events: auto;">Ok</button>
            </div>
        </div>
      </div>
    `;
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = document.getElementById(modalId);
    const okBtn = document.getElementById(okId);
    const modalContent = modal.querySelector('.modal-content');
    let resolved = false;
    let resolveFn = resolve;
    
    // Safety timeout - auto-close after 60 seconds
    const safetyTimeout = setTimeout(() => {
      if (!resolved) {
        closeModal(false);
      }
    }, 60000);
    
    // Helper to close modal
    const closeModal = (result) => {
      if (resolved) return;
      resolved = true;
      
      // Clear the safety timeout
      clearTimeout(safetyTimeout);
      
      // Remove the modal immediately
      if (modal && modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
      
      // Resolve the promise
      resolveFn(result);
    };
    
    // Stop propagation on modal content
    if (modalContent) {
      modalContent.addEventListener('click', (e) => {
        e.stopPropagation();
      });
    }
    
    // Handle ok button
    okBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeModal(true);
    });
    
    // Handle clicking outside modal
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(false);
      }
    });
  });
}

// Make dialogs globally accessible
globalThis.showConfirmDialog = showConfirmDialog;
globalThis.showAlertDialog = showAlertDialog;