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

function convSideNames(legacyname) {
  switch (legacyname.toLowerCase()) {
    case "up":
      return "top"
    case "down":
      return "bottom"
    case "left":
      return "left"
    case "right":
      return "right"
    default:
      return legacyname.toLowerCase()
  }
}

async function convertLegacyApollonModel(model) {
  if (!model || model.nodes || model.edges) {
    return model
  }

  let version = "4.0.0"
  let type = (model.type || "")
  let title = "Class Diagram"

  let elements = model.elements || {}
  let relationships = model.relationships || {}

  let nodes = []
  let edges = []

  // Collect attributes and methods keyed by owner
  let attrByOwner = {}
  let methodByOwner = {}

  Object.keys(elements).forEach(function (key) {
    let el = elements[key]
    if (!el?.type) return
    let type = (el.type || "")
    if (type === "ClassAttribute") {
      let owner = el.owner
      attrByOwner[owner] = attrByOwner[owner] || []
      attrByOwner[owner].push({ id: el.id, name: el.name || "" })
    } else if (type === "ClassMethod") {
      let ownerMeth = el.owner
      methodByOwner[ownerMeth] = methodByOwner[ownerMeth] || []
      methodByOwner[ownerMeth].push({ id: el.id, name: el.name || "" })
    }
  })

  Object.keys(elements).forEach(function (key) {
    let el = elements[key]
    if (!el?.type) return
    let type = (el.type || "")
    if (type.toLowerCase() === "class") {
      let width = el.bounds?.width || 160
      let height = el.bounds?.height || 70
      nodes.push({
        id: el.id,
        type: "class",
        position: { x: el.bounds?.x || 0, y: el.bounds?.y || 0 },
        width: width,
        height: height,
        data: {
          name: el.name || "",
          attributes: attrByOwner[el.id] || [],
          methods: methodByOwner[el.id] || [],
        },
        measured: { width: width, height: height },
      })
    }
  })

  Object.keys(relationships).forEach(function (key) {
    let rel = relationships[key]
    if (!rel?.type) return
    let type = (rel.type || "ClassBidirectional")
    let data = {}
    if (rel.source?.multiplicity) { data.sourceMultiplicity = rel.source.multiplicity }
    if (rel.source?.role) { data.sourceRole = rel.source.role }
    if (rel.target?.multiplicity) { data.targetMultiplicity = rel.target.multiplicity }
    if (rel.target?.role) { data.targetRole = rel.target.role }
    if (Array.isArray(rel.path)) { data.points = rel.path }

    let edge = {
      id: rel.id,
      type: type,
      source: rel.source?.element,
      target: rel.target?.element,
      data: data,
      sourceHandle: convSideNames(rel.source?.direction) || "right",
      targetHandle: convSideNames(rel.target?.direction) || "left"
    }
    edges.push(edge)
  })

  let data = { version: version, type: type, title: title, nodes: nodes, edges: edges, assessments: {} };
  return data;
}

// Forces a redraw by reloading a snapshot after a short delay, emulating the user download/reupload workaround.
async function refreshApollonEditor(bridge, modelOverride) {
  let snapshot
  try {
    snapshot = JSON.parse(JSON.stringify(modelOverride || bridge.model()))
  } catch (e) {
    console.warn("Apollon refresh: failed to copy model", e)
    return
  }

  await new Promise(function (resolve) {
    requestAnimationFrame(resolve)
  })

  try {
    bridge.loadModel(snapshot)
  } catch (e) {
    console.warn("Apollon refresh: failed to reload model", e)
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
    triggerUpload()
  })
})

async function triggerUpload() {
  let fileInput = document.getElementById("json_file")
  if (fileInput.files.length < 1) {
    showAlertDialog(
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
    showAlertDialog(
      "Datei ist zu groß. Maximale Dateigröße: " + UPLOAD_MAX_HUMAN,
      "fas fa-exclamation-triangle",
      "var(--accent-warning)"
    )
    fileInput.value = null
    return
  }

  let reader = new FileReader()
  reader.onload = async function (event) {
    try {
      let json = JSON.parse(event.target.result)
      json = await convertLegacyApollonModel(json)
      let bridge = await apollonReady
      bridge.loadModel(json)
      await refreshApollonEditor(bridge, json)
      sessionStorage.setItem('loaded_model', JSON.stringify(bridge.model()));
      await showAlertDialog(
        "Klassendiagramm wurde erfolgreich in den Editor geladen.",
        "fas fa-check-square",
        "var(--accent-success)"
      )
      //globalThis.location.reload()
    } catch (err) {
      showAlertDialog(
        "Fehler beim Laden der JSON-Datei: " + err.message,
        "fas fa-exclamation-triangle",
        "var(--accent-danger)"
      )
    }
  }
  reader.readAsText(file, "utf-8")
  fileInput.value = null
}



async function saveDiagram() {
  let bridge = await apollonReady
  let json = bridge.model()

  let confirmed = await showConfirmDialog(
    "Klassendiagramm auf dem Server speichern? Bestehendes Diagramm wird überschrieben, die Datenbank bleibt unverändert. Wenn du die Seite wechselst, ohne zu speichern, gehen deine Änderungen verloren!",
    "fas fa-save"
  )
  if (!confirmed) {
    return
  }

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/editor_diagram.json", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
    body: JSON.stringify(json),
  }).then(async function (response) {
    if (response.ok) {
      await showAlertDialog(
        "Klassendiagramm wurde erfolgreich auf dem Server gespeichert.",
        "fas fa-check-square",
        "var(--accent-success)"
      )
    } else {
      showAlertDialog(
        "Fehler beim Speichern des Klassendiagramms auf dem Server. Überprüfe, ob das Format deines Diagramms korrekt ist!",
        "fas fa-exclamation-triangle",
        "var(--accent-danger)"
      )
    }
  })
}

async function loadToDB() {
  let bridge = await apollonReady
  let json = bridge.model()

  let confirmed = await showConfirmDialog(
    "Achtung, hierdurch wird deine aktuelle Datenbank vollständig gelöscht! Das kann nicht rückgängig gemacht werden!",
    "fas fa-database"
  )
  if (!confirmed) {
    return
  }

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/db_diagram.json", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
    body: JSON.stringify(json),
  }).then(async function (response) {
    if (response.ok) {
      await showAlertDialog(
        "Klassendiagramm wurde als Datenbank geladen. Überprüfe in der Übersicht, ob automatisch Fehler korrigiert wurden!",
        "fas fa-check-square",
        "var(--accent-success)"
      )
      globalThis.location.href = "/overview?open=2"
    } else {
      showAlertDialog(
        "Fehler beim Laden des Klassendiagramms als Datenbank. Überprüfe, ob das Format deines Diagramms korrekt ist!",
        "fas fa-exclamation-triangle",
        "var(--accent-danger)"
      )
    }
  })
}

async function downloadJson() {
  let bridge = await apollonReady
  let json = bridge.model()

  let blob = new Blob([JSON.stringify(json)], { type: "application/json" })
  let url = URL.createObjectURL(blob)
  let a = document.createElement("a")
  a.href = url
  a.download = "diagram.json"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadSvg() {
  let bridge = await apollonReady
  let blob = await bridge.exportSvg()
  let url = URL.createObjectURL(blob)
  let a = document.createElement("a")
  a.href = url
  a.download = "diagram.svg"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadPng() {
  let bridge = await apollonReady
  let svgBlob = await bridge.exportSvg()
  let svgText = await svgBlob.text()
  let img = new Image()
  let svgUrl = URL.createObjectURL(new Blob([svgText], { type: "image/svg+xml" }))
  img.onload = function () {
    let canvas = document.createElement("canvas")
    canvas.width = img.width
    canvas.height = img.height
    let ctx = canvas.getContext("2d")
    if (ctx) {
      ctx.drawImage(img, 0, 0)
      canvas.toBlob(function (blob) {
        if (!blob) {
          return
        }
        let url = URL.createObjectURL(blob)
        let a = document.createElement("a")
        a.href = url
        a.download = "diagram.png"
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      })
    }
    URL.revokeObjectURL(svgUrl)
  }
  img.onerror = function () {
    showAlertDialog(
      "PNG Export fehlgeschlagen. Bitte nutze SVG.",
      "fas fa-exclamation-triangle",
      "orange"
    )
  }
  img.src = svgUrl
}

async function loadDbToEditor() {
  let confirmation = await showConfirmDialog(
    "Achtung, hierdurch wird das Diagramm im Editor unwiderruflich gelöscht und durch das deiner aktuellen Datenbank ersetzt.",
    "fas fa-project-diagram"
  )
  if (!confirmation) {
    return
  }
  loadDBJsonFromServer()
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
        let json = await convertLegacyApollonModel(data)
        let bridge = await apollonReady
        bridge.loadModel(json)
        await refreshApollonEditor(bridge, json)
        sessionStorage.setItem('loaded_model', JSON.stringify(bridge.model()));
          showAlertDialog(
            "Datenbank-Klassendiagramm erfolgreich in den Editor geladen.",
            "fas fa-check-square",
            "var(--accent-success)"
          )
      } catch (err) {
        showAlertDialog(
          "Fehler beim Laden des Diagramms: " + err.message,
          "fas fa-exclamation-triangle",
          "var(--accent-danger)"
        )
      }
    })
    .catch(function () {
      showAlertDialog(
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
        let json = await convertLegacyApollonModel(data)
        let bridge = await apollonReady
        bridge.loadModel(json)
        await refreshApollonEditor(bridge, json)
        sessionStorage.setItem('loaded_model', JSON.stringify(bridge.model()));
        if (manuallyTriggered) {
          showAlertDialog(
            "Gespeichertes Klassendiagramm erfolgreich in den Editor geladen.",
            "fas fa-check-square",
            "var(--accent-success)"
          )
        }
      } catch (err) {
        showAlertDialog(
          "Fehler beim Laden des Diagramms: " + err.message,
          "fas fa-exclamation-triangle",
          "var(--accent-danger)"
        )
      }
    })
    .catch(function () {
      showAlertDialog(
        "Es konnte kein bestehendes Klassendiagramm vom Server geladen werden. Wenn du noch nie ein Klassendiagramm als Datenbank importiert hast, ist das normal. Ansonsten kannst du die Seite neu laden, dann erscheint dein Diagramm automatisch.",
        "fas fa-exclamation-triangle",
        "orange"
      )
    })
}

loadEditorJsonFromServer(false)

// Save the current diagram before navigating away so changes are not lost.
let apollonNavigationSaveInProgress = false

function shouldInterceptApollonNavigation(anchor, event) {
  if (!anchor || !anchor.href) return false
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
  saveDiagramAndNavigate(anchor.href)
})

