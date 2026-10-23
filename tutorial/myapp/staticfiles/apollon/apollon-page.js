let APOLLON_CONFIG = globalThis.apollonPageConfig || {}
let UPLOAD_MAX_BYTES =
  typeof APOLLON_CONFIG.uploadMaxBytes === "number"
    ? APOLLON_CONFIG.uploadMaxBytes
    : null
let UPLOAD_MAX_HUMAN = APOLLON_CONFIG.uploadMaxHuman || ""

let apollonReady = (globalThis.apollon2Ready =
  globalThis.apollon2Ready ||
  new Promise(function (resolve) {
    if (globalThis.apollon2) {
      resolve(globalThis.apollon2)
    } else {
      globalThis._apollon2ReadyResolve = resolve
    }
  }))

// Tracks edits made in the editor since the diagram was last loaded or saved,
// so leaving the page only asks to save when there is something to lose.
// Compares user-editable content only: sizes and edge geometry are derived
// by the editor and may be corrected right after a load.
let apollonDirty = false
let apollonBaseline = null

function apollonContentKey(model) {
  return JSON.stringify({
    nodes: (model.nodes || []).map(function (n) {
      return [n.id, n.type, Math.round(n.position?.x), Math.round(n.position?.y), n.data]
    }),
    edges: (model.edges || []).map(function (e) {
      let data = { ...e.data }
      delete data.points
      return [e.id, e.type, e.source, e.target, e.sourceHandle, e.targetHandle, data]
    }),
  })
}

function markApollonClean(model) {
  apollonBaseline = apollonContentKey(model)
  apollonDirty = false
}

// For diagrams that are in the editor but not on the server yet.
function markApollonUnsaved() {
  apollonBaseline = ""
  apollonDirty = true
}

apollonReady.then(function (bridge) {
  markApollonClean(bridge.model())
  bridge.onModelChange(function (model) {
    if (apollonBaseline !== null) {
      apollonDirty = apollonContentKey(model) !== apollonBaseline
    }
  })
})

// Loads a diagram (Apollon v2, v3 or v4 JSON) into the editor and takes it as
// the new unchanged state once the editor has settled.
async function loadIntoEditor(json) {
  let bridge = await apollonReady
  apollonBaseline = null
  try {
    bridge.loadModel(json)
  } finally {
    await new Promise(function (resolve) {
      requestAnimationFrame(function () {
        setTimeout(resolve, 100)
      })
    })
    markApollonClean(bridge.model())
  }
}

document.addEventListener("DOMContentLoaded", function () {
  let dropZone = document.getElementById("drop-zone")
  let fileInput = document.getElementById("json_file")

  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault()
    e.dataTransfer.dropEffect = "copy"
  })

  dropZone.addEventListener("drop", function (e) {
    e.preventDefault()
    fileInput.files = e.dataTransfer.files
    void triggerUpload()
  })
})

async function triggerUpload() {
  let fileInput = document.getElementById("json_file")
  if (fileInput.files.length < 1) {
    void showAlertDialog(
      "Keine Datei zum Upload ausgewählt. Wähle mit 'Browse...' eine Datei zum Upload aus oder ziehe sie per Drag'n'Drop in den gestrichelten Kasten."
    )
    return
  }

  let confirmed = await showConfirmDialog(
    "Achtung, hierdurch wird das aktuelle Klassendiagramm gelöscht! Die Datenbank wird nicht verändert.",
    "fas fa-project-diagram"
  )
  if (!confirmed) {
    return
  }

  let file = fileInput.files[0]
  if (UPLOAD_MAX_BYTES && file.size > UPLOAD_MAX_BYTES) {
    void showAlertDialog(
      "Datei ist zu groß. Maximale Dateigröße: " + UPLOAD_MAX_HUMAN,
      "fas fa-exclamation-triangle",
      "var(--accent-warning)"
    )
    fileInput.value = null
    return
  }

  let reader = new FileReader()
  reader.onload = function (event) {
    void loadUploadedFile(event.target.result)
  }
  reader.readAsText(file, "utf-8")
  fileInput.value = null
}

async function loadUploadedFile(text) {
  try {
    await loadIntoEditor(JSON.parse(text))
    // The uploaded diagram is not on the server yet.
    markApollonUnsaved()
    await showAlertDialog(
      "Klassendiagramm wurde erfolgreich in den Editor geladen.",
      "fas fa-check-square",
      "var(--accent-success)"
    )
  } catch (err) {
    void showAlertDialog(
      "Fehler beim Laden der JSON-Datei: " + err.message,
      "fas fa-exclamation-triangle",
      "var(--accent-danger)"
    )
  }
}

// Resolves to true when the diagram was stored on the server.
async function saveDiagram(force = false) {
  let bridge = await apollonReady
  let json = bridge.model()

  if (!force) {
    let confirmed = await showConfirmDialog(
      "Klassendiagramm auf dem Server speichern? Bestehendes Diagramm wird überschrieben, die Datenbank bleibt unverändert. Wenn du die Seite wechselst, ohne zu speichern, gehen deine Änderungen verloren!",
      "fas fa-save"
    )
    if (!confirmed) {
      return false
    }
  }

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  let saved = false
  try {
    let response = await fetch("/api/editor_diagram.json", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
      body: JSON.stringify(json),
    })
    saved = response.ok
  } catch (err) {
    console.warn("Apollon save failed", err)
  }

  if (saved) {
    markApollonClean(json)
    if (!force) {
      await showAlertDialog(
        "Klassendiagramm wurde erfolgreich auf dem Server gespeichert.",
        "fas fa-check-square",
        "var(--accent-success)"
      )
    }
    return true
  }

  await showAlertDialog(
    "Fehler beim Speichern des Klassendiagramms auf dem Server. Überprüfe, ob das Format deines Diagramms korrekt ist!",
    "fas fa-exclamation-triangle",
    "var(--accent-danger)"
  )
  return false
}

async function loadToDB() {
  let bridge = await apollonReady
  let json = bridge.model()

  let confirmed = await showConfirmDialog(
    "Achtung, hierdurch wird deine aktuelle Datenbank vollständig gelöscht! Das kann nicht rückgängig gemacht werden! Das Klassendiagramm wird außerdem einzeln gespeichert.",
    "fas fa-database"
  )
  if (!confirmed) {
    return
  }

  await saveDiagram(true)

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  let loaded = false
  try {
    let response = await fetch("/api/db_diagram.json", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
      body: JSON.stringify(json),
    })
    loaded = response.ok
  } catch (err) {
    console.warn("Apollon diagram to DB failed", err)
  }

  if (loaded) {
    await showAlertDialog(
      "Klassendiagramm wurde als Datenbank geladen. Überprüfe in der Übersicht, ob automatisch Fehler korrigiert wurden!",
      "fas fa-check-square",
      "var(--accent-success)"
    )
    globalThis.location.href = "/overview?open=2"
  } else {
    await showAlertDialog(
      "Fehler beim Laden des Klassendiagramms als Datenbank. Überprüfe, ob das Format deines Diagramms korrekt ist!",
      "fas fa-exclamation-triangle",
      "var(--accent-danger)"
    )
  }
}

function downloadBlob(blob, filename) {
  let url = URL.createObjectURL(blob)
  let a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function downloadExport(exporter, filename, label) {
  try {
    let bridge = await apollonReady
    downloadBlob(await exporter(bridge), filename)
  } catch (err) {
    console.warn("Apollon export failed", err)
    void showAlertDialog(
      label + " Export fehlgeschlagen: " + err.message,
      "fas fa-exclamation-triangle",
      "var(--accent-warning)"
    )
  }
}

async function downloadJson() {
  await downloadExport(
    function (bridge) {
      return new Blob([JSON.stringify(bridge.model())], {
        type: "application/json",
      })
    },
    "diagram.json",
    "JSON"
  )
}

async function downloadSvg() {
  await downloadExport(
    function (bridge) {
      return bridge.exportSvg()
    },
    "diagram.svg",
    "SVG"
  )
}

async function downloadPng() {
  await downloadExport(
    function (bridge) {
      return bridge.exportPng()
    },
    "diagram.png",
    "PNG"
  )
}

async function downloadPdf() {
  await downloadExport(
    function (bridge) {
      return bridge.exportPdf()
    },
    "diagram.pdf",
    "PDF"
  )
}

async function loadDbToEditor() {
  let confirmation = await showConfirmDialog(
    "Achtung, hierdurch wird das Diagramm im Editor unwiderruflich gelöscht und durch das deiner aktuellen Datenbank ersetzt.",
    "fas fa-project-diagram"
  )
  if (!confirmation) {
    return
  }
  void loadDBJsonFromServer()
}

async function loadDBJsonFromServer() {
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/db_diagram.json", {
    method: "GET",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
  })
    .then(function (response) {
      return response.json()
    })
    .then(async function (data) {
      try {
        await loadIntoEditor(data)
        // The editor now differs from the diagram saved on the server.
        markApollonUnsaved()
        void showAlertDialog(
          "Datenbank-Klassendiagramm erfolgreich in den Editor geladen.",
          "fas fa-check-square",
          "var(--accent-success)"
        )
      } catch (err) {
        void showAlertDialog(
          "Fehler beim Laden des Diagramms: " + err.message,
          "fas fa-exclamation-triangle",
          "var(--accent-danger)"
        )
      }
    })
    .catch(function () {
      void showAlertDialog(
        "Es konnte kein bestehendes Klassendiagramm vom Server geladen werden. Wenn du noch nie ein Klassendiagramm als Datenbank importiert hast, ist das normal. Ansonsten kannst du die Seite neu laden, dann erscheint dein Diagramm automatisch.",
        "fas fa-exclamation-triangle",
        "var(--accent-warning)"
      )
    })
}

async function loadEditorJsonFromServer(manuallyTriggered) {
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/editor_diagram.json", {
    method: "GET",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
  })
    .then(function (response) {
      return response.json()
    })
    .then(async function (data) {
      try {
        await loadIntoEditor(data)
        if (manuallyTriggered) {
          void showAlertDialog(
            "Gespeichertes Klassendiagramm erfolgreich in den Editor geladen.",
            "fas fa-check-square",
            "var(--accent-success)"
          )
        }
      } catch (err) {
        void showAlertDialog(
          "Fehler beim Laden des Diagramms: " + err.message,
          "fas fa-exclamation-triangle",
          "var(--accent-danger)"
        )
      }
    })
    .catch(function () {
      void showAlertDialog(
        "Es konnte kein bestehendes Klassendiagramm vom Server geladen werden. Wenn du noch nie ein Klassendiagramm als Datenbank importiert hast, ist das normal. Ansonsten kannst du die Seite neu laden, dann erscheint dein Diagramm automatisch.",
        "fas fa-exclamation-triangle",
        "orange"
      )
    })
}

// Wait for DOMContentLoaded: the dialog helpers come from the sqlution.js
// module, which only runs after this classic script.
document.addEventListener("DOMContentLoaded", function () {
  void loadEditorJsonFromServer(false)
})

// Offer to save unsaved changes before navigating away so they are not lost.
let apollonNavigationSaveInProgress = false

function shouldInterceptApollonNavigation(anchor, event) {
  if (!apollonDirty) return false
  if (!anchor?.href) return false
  if (event && (event.ctrlKey || event.metaKey || event.button === 1)) return false
  if (anchor.hasAttribute("download")) return false
  let targetAttr = anchor.getAttribute("target")
  if (targetAttr && targetAttr !== "" && targetAttr !== "_self") return false
  let href = anchor.getAttribute("href")
  if (!href || href.charAt(0) === "#") return false
  if (href.toLowerCase().startsWith("javascript:")) return false
  return true
}

async function saveDiagramAndNavigate(targetHref) {
  if (apollonNavigationSaveInProgress) return
  apollonNavigationSaveInProgress = true
  try {
    await saveDiagram()
  } catch (err) {
    console.warn("Apollon navigation save failed", err)
  } finally {
    globalThis.location.href = targetHref
  }
}

document.addEventListener("click", function (event) {
  let anchor = event.target.closest("a")
  if (!shouldInterceptApollonNavigation(anchor, event)) return
  event.preventDefault()
  void saveDiagramAndNavigate(anchor.href)
})
