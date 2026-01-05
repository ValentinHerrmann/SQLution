var APOLLON_CONFIG = window.apollonPageConfig || {}
var UPLOAD_MAX_BYTES =
  typeof APOLLON_CONFIG.uploadMaxBytes === "number"
    ? APOLLON_CONFIG.uploadMaxBytes
    : null
var UPLOAD_MAX_HUMAN = APOLLON_CONFIG.uploadMaxHuman || ""

var apollonReady = (window.apollon2Ready =
  window.apollon2Ready ||
  new Promise(function (resolve) {
    if (window.apollon2) {
      resolve(window.apollon2)
    } else {
      window._apollon2ReadyResolve = resolve
    }
  }))

document.addEventListener("DOMContentLoaded", function () {
  var dropZone = document.getElementById("drop-zone")
  var fileInput = document.getElementById("json_file")

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
  var fileInput = document.getElementById("json_file")
  if (fileInput.files.length < 1) {
    showAlertDialog(
      "Keine Datei zum Upload ausgewählt. Wähle mit 'Browse...' eine Datei zum Upload aus oder ziehe sie per Drag'n'Drop in den gestrichelten Kasten."
    )
    return
  }

  var confirmed = await showConfirmDialog(
    "Achtung, hierdurch wird das aktuelle Klassendiagramm gelöscht! Die Datenbank wird nicht verändert.",
    "fas fa-project-diagram"
  )
  if (!confirmed) {
    return
  }

  var file = fileInput.files[0]
  if (UPLOAD_MAX_BYTES && file.size > UPLOAD_MAX_BYTES) {
    showAlertDialog(
      "Datei ist zu groß. Maximale Dateigröße: " + UPLOAD_MAX_HUMAN,
      "fas fa-exclamation-triangle",
      "red"
    )
    fileInput.value = null
    return
  }

  var reader = new FileReader()
  reader.onload = async function (event) {
    try {
      var json = JSON.parse(event.target.result)
      var bridge = await apollonReady
      bridge.loadModel(json)
      await showAlertDialog(
        "Klassendiagramm wurde erfolgreich in den Editor geladen.",
        "fas fa-check-square",
        "green"
      )
    } catch (err) {
      showAlertDialog(
        "Fehler beim Laden der JSON-Datei: " + err.message,
        "fas fa-exclamation-triangle",
        "red"
      )
    }
  }
  reader.readAsText(file, "utf-8")
  fileInput.value = null
}

async function loadToDB() {
  var bridge = await apollonReady
  var json = bridge.model()

  var confirmed = await showConfirmDialog(
    "Achtung, hierdurch wird deine aktuelle Datenbank vollständig gelöscht! Das kann nicht rückgängig gemacht werden!",
    "fas fa-database"
  )
  if (!confirmed) {
    return
  }

  var csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/diagram.json", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
    body: JSON.stringify(json),
  }).then(async function (response) {
    if (response.ok) {
      await showAlertDialog(
        "Klassendiagramm wurde als Datenbank geladen. Überprüfe in der Übersicht, ob automatisch Fehler korrigiert wurden!",
        "fas fa-check-square",
        "green"
      )
      window.location.href = "/overview?open=2"
    } else {
      showAlertDialog(
        "Fehler beim Laden des Klassendiagramms als Datenbank. Überprüfe, ob das Format deines Diagramms korrekt ist!",
        "fas fa-exclamation-triangle",
        "red"
      )
    }
  })
}

async function downloadJson() {
  var bridge = await apollonReady
  var json = bridge.model()

  var blob = new Blob([JSON.stringify(json)], { type: "application/json" })
  var url = URL.createObjectURL(blob)
  var a = document.createElement("a")
  a.href = url
  a.download = "diagram.json"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadSvg() {
  var bridge = await apollonReady
  var blob = await bridge.exportSvg()
  var url = URL.createObjectURL(blob)
  var a = document.createElement("a")
  a.href = url
  a.download = "diagram.svg"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadPng() {
  var bridge = await apollonReady
  var svgBlob = await bridge.exportSvg()
  var svgText = await svgBlob.text()
  var img = new Image()
  var svgUrl = URL.createObjectURL(new Blob([svgText], { type: "image/svg+xml" }))
  img.onload = function () {
    var canvas = document.createElement("canvas")
    canvas.width = img.width
    canvas.height = img.height
    var ctx = canvas.getContext("2d")
    if (ctx) {
      ctx.drawImage(img, 0, 0)
      canvas.toBlob(function (blob) {
        if (!blob) {
          return
        }
        var url = URL.createObjectURL(blob)
        var a = document.createElement("a")
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
  var confirmation = await showConfirmDialog(
    "Achtung, hierdurch wird das Diagramm im Editor unwiderruflich gelöscht und durch das deiner aktuellen Datenbank ersetzt.",
    "fas fa-project-diagram"
  )
  if (!confirmation) {
    return
  }

  loadJsonFromServer(true)
}

async function loadJsonFromServer(manuallyTriggered) {
  var csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value
  fetch("/api/diagram.json", {
    method: "GET",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
  })
    .then(function (response) {
      return response.json()
    })
    .then(async function (data) {
      var bridge = await apollonReady
      bridge.loadModel(data)
      if (manuallyTriggered) {
        showAlertDialog(
          "Klassendiagramm wurde erfolgreich in den Editor geladen.",
          "fas fa-check-square",
          "green"
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

loadJsonFromServer(false)
