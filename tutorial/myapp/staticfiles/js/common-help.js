/* =================================================================
   COMMON JAVASCRIPT FOR HELP OVERLAYS
   Handles opening/closing of help popup overlays
   ================================================================= */

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // Attach to all buttons that declare a data-help-overlay attribute
    let buttons = document.querySelectorAll('[data-help-overlay]')
    let overlayEntries = []

    buttons.forEach(function (btn) {
      let selector = btn.dataset.helpOverlay
      let overlay = selector ? document.querySelector(selector) : null
      if (!overlay) return

      let closeBtn = overlay.querySelector('.help-overlay-close')
      let entry = { btn: btn, overlay: overlay, closeBtn: closeBtn }
      overlayEntries.push(entry)

      btn.addEventListener('click', function (e) {
        e.preventDefault()
        // toggle this overlay
        entry.overlay.hidden = !entry.overlay.hidden
      })

      if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
          e.preventDefault()
          entry.overlay.hidden = true
        })
      }
    })

    // Global click handler: close any open overlay when clicking outside
    document.addEventListener('click', function (e) {
      let target = e.target
      overlayEntries.forEach(function (entry) {
        if (entry.overlay.hidden) return
        if (entry.overlay.contains(target)) return
        if (entry.btn.contains(target)) return
        entry.overlay.hidden = true
      })
    })
  })
})()
