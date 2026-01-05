(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // Attach to all buttons that declare a data-help-overlay attribute.
    var buttons = document.querySelectorAll('[data-help-overlay]')
    var overlayEntries = []

    buttons.forEach(function (btn) {
      var selector = btn.dataset.helpOverlay
      var overlay = selector ? document.querySelector(selector) : null
      if (!overlay) return

      var closeBtn = overlay.querySelector('.db-help-overlay-close')
      var entry = { btn: btn, overlay: overlay, closeBtn: closeBtn }
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

    // Global click handler: close any open overlay when clicking outside overlay and its opener
    document.addEventListener('click', function (e) {
      var target = e.target
      overlayEntries.forEach(function (entry) {
        if (entry.overlay.hidden) return
        if (entry.overlay.contains(target)) return
        if (entry.btn.contains(target)) return
        entry.overlay.hidden = true
      })
    })
  })
})()
