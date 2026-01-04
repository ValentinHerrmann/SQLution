// SQL IDE client-side logic: Ace initialization, file explorer and save handlers
(function () {
  let filenameOnLoad = "";
  let contentOnLoad = "";
  let prevEditorHeight = null;

  function initAce() {
    try {
      ace.require("ace/ext/language_tools");
      const editor = ace.edit("editor");
      editor.setTheme("ace/theme/twilight");
      editor.session.setMode("ace/mode/sql");
      globalThis.sqlAceEditor = editor;
      editor.setOptions({
        enableBasicAutocompletion: true,
        enableSnippets: true,
        enableLiveAutocompletion: false,
      });
      globalThis.sqlAceEditor.setValue("");
    } catch (err) {
      console.error('Error initializing ACE editor:', err);
    }
  }

  // File explorer functions
  async function loadFileList() {
    const ul = document.getElementById('file-list');
    if (!ul) return;
    ul.innerHTML = '<li style="padding:0.8rem; color:var(--text-secondary);">Lade Dateien…</li>';
    try {
      const resp = await fetch('/api/sql/list');
      if (!resp.ok) throw new Error('Could not load file list');
      const data = await resp.json();
      let files = data.files || [];
      files.unshift('Playground');
      if (files.length === 0) {
        ul.innerHTML = '<li style="padding:0.8rem; color:var(--text-secondary);">Keine SQL-Dateien gefunden.</li>';
        return;
      }
      ul.innerHTML = '';
      let firstLi = null;
      let idx = 0;
      for (const f of files) {
        const li = document.createElement('li');
        li.style.display = 'flex';
        li.style.justifyContent = 'space-between';
        li.style.alignItems = 'center';
        li.style.padding = '0.6rem 0.8rem';
        li.style.cursor = 'pointer';
        li.style.borderBottom = '1px solid var(--border)';

        const nameSpan = document.createElement('span');
        nameSpan.textContent = f;
        nameSpan.style.flex = '1 1 auto';

        let delBtn = null;
        if(f !== 'Playground') {
          delBtn = document.createElement('button');
          delBtn.type = 'button';
          delBtn.title = 'Löschen';
          delBtn.innerHTML = '<i class="fas fa-trash" aria-hidden="true"></i>';
          delBtn.style.marginLeft = '0.5rem';
          delBtn.style.background = 'transparent';
          delBtn.style.border = 'none';
          delBtn.style.color = 'var(--text-danger)';
          delBtn.style.cursor = 'pointer';
          delBtn.style.display = 'none';
          // Delete handler (stop propagation so it doesn't trigger load)
          delBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const ok = await globalThis.showConfirmDialog(
            `Datei "${f}" wirklich löschen?`,
            "fas fa-trash"
          );
          if (!ok) return;
          try {
            const base = f.replace(/\.sql$/i, '');
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const resp = await fetch(`/api/sql/${encodeURIComponent(base)}.sql`, { method: 'DELETE', headers: csrftoken ? { 'X-CSRFToken': csrftoken } : {} });
            if (resp.ok) {
              // if deleted file was open, clear editor
              if (filenameOnLoad === f) {
                const editor = globalThis.sqlAceEditor;
                if (editor) editor.setValue('', -1);
                filenameOnLoad = '';
                contentOnLoad = '';
              }
              // refresh list
              await loadFileList();
            } else {
              alert('Fehler beim Löschen der Datei.');
            }
          } catch (err) {
            console.error('Delete error', err);
            alert('Fehler beim Löschen der Datei.');
          }
        });
        }

        // Clicking the li loads the file
        li.addEventListener('click', () => loadFileIntoEditor(f, li));

        

        li.appendChild(nameSpan);
        if(f !== 'Playground') {
          if(delBtn) {
            li.appendChild(delBtn);
          }
        }
        ul.appendChild(li);
        if (idx === 0) firstLi = li;
        idx++;
      }
      // automatically open first file
      if (firstLi) loadFileIntoEditor(files[0], firstLi);
    } catch (err) {
      ul.innerHTML = '<li style="padding:0.8rem; color:var(--text-danger);">Fehler beim Laden der Dateien.</li>';
      console.error(err);
    }
  }

  async function saveFile(filename, content) {
    try {
      console.log("Saving file: " + filename);
      const base = filename.replace(/\.sql$/i, '');
      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      const url = `/api/sql/${encodeURIComponent(base)}.sql`;
      const headers = { "Content-Type": "application/json" };
      if (csrftoken) headers['X-CSRFToken'] = csrftoken;
      const body = JSON.stringify({ sql: content });

      const resp = await fetch(url, {
        method: "POST",
        headers: headers,
        body: body
      });

      if (resp.ok) {
        console.debug("File saved successfully: " + filename);
        return true;
      } else {
        console.error("Fehler beim Speichern der SQL Datei.", resp.status, resp.statusText);
        return false;
      }
    } catch (err) {
      console.error('Error saving file:', err);
      return false;
    }
  }

  async function saveCurrentFile() {
    const editor = globalThis.sqlAceEditor;
    if (!editor) {
      console.error('Editor not initialized');
      return false;
    }
    const content = editor.getValue();
    if (!filenameOnLoad) {
      console.error('No file loaded to save');
      return false;
    }
    if(filenameOnLoad === 'Playground') {
      globalThis.showAlertDialog("Der Playground kann nicht gespeichert werden. Bitte erstelle eine neue SQL-Datei über das '+'-Symbol im Dateiexplorer.", "fas fa-exclamation-triangle");
      return false;
    }

    console.log("Content to save: " + content);
    console.log("Filename to save: " + filenameOnLoad);
    return await saveFile(filenameOnLoad, content);
  }

  async function loadFileIntoEditor(filename, liElement) {
    try {
      // restore editor height when opening a file (remove result view)
      restoreEditorHeight();

      const editor = globalThis.sqlAceEditor;
      if (!editor) throw new Error('Editor not initialized');

      if (editor.getValue() !== contentOnLoad) {
        if(filenameOnLoad === 'Playground') {
          sessionStorage.setItem('sql_playground', editor.getValue());
        }
        else {
          const confirmed = await globalThis.showConfirmDialog(
            "Änderungen speichern? Wenn nicht gespeichert wird, gehen diese verloren.",
            "fas fa-save"
          );
          if (confirmed) {
            if(filenameOnLoad !== 'Playground') {
              let success = await saveCurrentFile();
              console.log("Save success: " + success);
              if (!success) {
                globalThis.showAlertDialog("Speichern der Datei fehlgeschlagen. Abbruch des Ladevorgangs.", "fas fa-exclamation-triangle");
                return;
              }
            }
          }
        }
      }

      // highlight selection and show delete button only for selected
      for (const el of document.querySelectorAll('#file-list li')) {
        el.style.background = '';
        const btn = el.querySelector('button');
        if (btn) btn.style.display = 'none';
      }
      if (liElement) {
        liElement.style.background = 'var(--text-muted)';
        const btn = liElement.querySelector('button');
        if (btn) btn.style.display = 'inline-block';
      }
      if(filename === 'Playground') {
        if (sessionStorage.getItem('sql_playground')) {
          const savedContent = sessionStorage.getItem('sql_playground');
          editor.setValue(savedContent, -1);
          contentOnLoad = savedContent;
          filenameOnLoad = filename;
          return;
        }
        const content = '-- Ein Playground ist eine Code-Umgebung zum Ausprobieren von SQL-Abfragen.\n-- Was du machst, wird gelöscht, sobald du dich abmeldest oder den Browser schließt.\n\n-- Um deine SQL-Abfragen zu speichern, erstelle eine neue SQL-Datei über das\n-- "+"-Symbol oben links im Dateiexplorer.\n\n\n';
        editor.setValue(content, -1);
        contentOnLoad = content;
        filenameOnLoad = filename;
        return;
      }
      else {
        const base = filename.replace(/\.sql$/i, '');
        const resp = await fetch(`/api/sql/${encodeURIComponent(base)}.sql`);
        if (!resp.ok) throw new Error('Could not load file content');
        const content = await resp.text();
        console.log("Load from file: " + content);
        editor.setValue(content, -1);
        contentOnLoad = content;
        filenameOnLoad = filename;
      }
    } catch (err) {
      console.error(err);
      globalThis.showAlertDialog('Fehler beim Laden der Datei. Siehe Konsole.', "fas fa-exclamation-triangle");
    }
  }

  async function saveSQLFiles() {
    console.log("Saving SQL files...");
    const confirmed = await globalThis.showConfirmDialog(
      "Das Speichern überschreibt alle SQL-Abfragen auf dem Server. Das kann nicht rückgängig gemacht werden!",
      "fas fa-save"
    );
    if (!confirmed) return;

    const editorElem = document.getElementById('editor');
    const username = editorElem?.dataset?.user || '';
    const ide = globalThis.sql_ide_access?.getIDE ? globalThis.sql_ide_access.getIDE(username) : null;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const sql_files = [];
    if (ide) {
      const files = ide.getFiles();
      for (const file of files) {
        const filename = file.getName();
        const content = file.getText();
        sql_files.push({ filename: filename, sql: content });
      }
    }

    try {
      const resp = await fetch('/api/sql/all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({ files: sql_files })
      });
      if (resp.ok) console.debug('Files saved successfully');
      else console.error('Fehler beim Speichern der Dateien.');
    } catch (err) {
      console.error('Error saving files list:', err);
    }
  }

  async function addSQLFileDialog() {
    let filename = prompt('Dateiname');
    if (!filename) return;
    if (!filename.toLowerCase().endsWith('.sql')) filename += '.sql';
    try {
      const base = filename.replace(/\.sql$/i, '');
      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      const url = `/api/sql/${encodeURIComponent(base)}.sql`;
      const headers = { "Content-Type": "application/json" };
      if (csrftoken) headers['X-CSRFToken'] = csrftoken;
      const body = JSON.stringify({ sql: "" });

      const resp = await fetch(url, {
        method: "PUT",
        headers: headers,
        body: body
      });

      if (resp.ok) {
        console.debug("File created successfully: " + filename);
      } else {
        console.error("Fehler beim Erstellen der SQL Datei.", resp.status, resp.statusText);
        globalThis.showAlertDialog("Fehler beim Erstellen der SQL Datei.", "fas fa-exclamation-triangle");
      }
    } catch (err) {
      console.error('Error creating file:', err);
      globalThis.showAlertDialog("Fehler beim Erstellen der SQL Datei.", "fas fa-exclamation-triangle");
    }
    loadFileList();
  }


    function escapeHtml(str) {
      if (str === null || str === undefined) return '';
      return String(str).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
    }

  async function parseErrorResponse(resp) {
    let errorMsg = `HTTP ${resp.status}`;
    try {
      const ct = resp.headers.get('content-type') || '';
      const bodyText = await resp.text();
      if (ct.includes('application/json')) {
        try {
          const jb = JSON.parse(bodyText);
          if (jb?.error) errorMsg = jb.error;
          else if (jb?.message) errorMsg = jb.message;
          else errorMsg = JSON.stringify(jb);
        } catch (e) {
          errorMsg = bodyText || errorMsg;
          console.error('Error parsing JSON error body', e);
        }
      } else {
        errorMsg = bodyText || errorMsg;
      }
    } catch (e) {
      console.error('Error reading error body', e);
    }
    return errorMsg;
  }

  function renderResultsTable(columns, rows, resultsContainer) {
    const table = document.createElement('table');
    table.setAttribute('border', '1');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginBottom = '20px';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    for (const col of columns) {
      const th = document.createElement('th');
      th.style.paddingLeft = '4px';
      th.textContent = col;
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (const r of rows) {
      const tr = document.createElement('tr');
      for (const cell of r) {
        const td = document.createElement('td');
        td.style.borderColor = 'var(--border-color)';
        td.style.paddingLeft = '4px';
        td.textContent = cell === null || cell === undefined ? '' : String(cell);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);

    resultsContainer.innerHTML = '';
    resultsContainer.appendChild(table);
  }

  // Run SQL from editor and render results into #sql-results
  async function runSqlFromEditor() {
    const editor = globalThis.sqlAceEditor;
    if (!editor) return;
    const sql = editor.getValue();

    const proceed = await warnIfDDL(sql);
    if(!proceed) { 
      return;
    }

    const resultsContainer = document.getElementById('sql-results');
    if (!resultsContainer) return;
    resultsContainer.innerHTML = '<div style="padding:8px;color:var(--text-secondary);">Ausführen…</div>';
    try {
      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
      const headers = { 'Content-Type': 'application/json' };
      if (csrftoken) headers['X-CSRFToken'] = csrftoken;
      const resp = await fetch('/api/sql/run', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ sql: sql })
      });
      if (!resp.ok) {
        const errorMsg = await parseErrorResponse(resp);
        resultsContainer.innerHTML = `<div style="padding:8px;color:var(--text-danger);">Fehler beim Ausführen der Abfrage: ${escapeHtml(errorMsg)}</div>`;
        console.error('Run SQL HTTP error', resp.status, errorMsg);
        setEditorHalf();
        return;
      }
      const data = await resp.json();
      if (data.error) {
        resultsContainer.innerHTML = `<div style="padding:8px;color:var(--text-danger);">Fehler: ${escapeHtml(data.error)}</div>`;
        setEditorHalf();
        return;
      }
      const columns = data.columns || [];
      const rows = data.result || [];
      renderResultsTable(columns, rows, resultsContainer);
      setEditorHalf();
    } catch (err) {
      console.error('Run SQL error', err);
      resultsContainer.innerHTML = `<div style="padding:8px;color:var(--text-danger);">Fehler beim Ausführen der Abfrage. Siehe Konsole.</div>`;
      setEditorHalf();
    }
  }

  // Adjust editor height to half the viewport and trigger Ace resize
  function setEditorHalf() {
    try {
      const editorElem = document.getElementById('editor');
      if (!editorElem) return;
      if (prevEditorHeight === null) prevEditorHeight = editorElem.style.height || globalThis.getComputedStyle(editorElem).height || '';
      editorElem.style.height = '50vh';
      const editor = globalThis.sqlAceEditor;
      if (editor && typeof editor.resize === 'function') editor.resize();
    } catch (e) {
      console.error('setEditorHalf error', e);
    }
  }

  // Restore editor height to previous value and trigger Ace resize
  function restoreEditorHeight() {
    try {
      const editorElem = document.getElementById('editor');
      if (!editorElem) return;
      if (prevEditorHeight !== null) {
        editorElem.style.height = prevEditorHeight;
        prevEditorHeight = null;
      }
      const editor = globalThis.sqlAceEditor;
      if (editor && typeof editor.resize === 'function') editor.resize();
    } catch (e) {
      console.error('restoreEditorHeight error', e);
    }
  }

  function checkDDL(query) {
    const ddlCommands = ['CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'RENAME'];
    const trimmedQuery = query.trim().toUpperCase();
    for (const cmd of ddlCommands) {
      if (trimmedQuery.includes(cmd + ' ')) {
        return true;
      }
    }
    return false;
  }

  async function warnIfDDL(query) {
    if (checkDDL(query)) {
      return await globalThis.showConfirmDialog(
        "Achtung: Diese Abfrage enthält DDL-Befehle (z.B. CREATE, ALTER, DROP). Diese Befehle verändern die Datenbankstruktur (ohne dabei das Klassendiagramm anzupassen) und können nicht rückgängig gemacht werden. Führe solche Befehle nur aus, wenn du weißt, was du tust!",
        "fas fa-exclamation-triangle"
      );
    }
    return true;
  }

  // Wire up events once DOM is ready
  document.addEventListener('DOMContentLoaded', function () {
    initAce();

    const syncBtn = document.getElementById('sync-sql-btn');
    if (syncBtn) syncBtn.addEventListener('click', loadFileList);

    const saveBtn = document.getElementById('save-sql-btn');
    if (saveBtn) saveBtn.addEventListener('click', saveCurrentFile);

    const addBtn = document.getElementById('add-sql-btn');
    if (addBtn) addBtn.addEventListener('click', addSQLFileDialog);

    const runBtn = document.getElementById('run-sql-btn');
    if (runBtn) runBtn.addEventListener('click', runSqlFromEditor);

    // load files if explorer exists
    if (document.getElementById('file-list')) loadFileList();

    // Only one <details> can be open at once
    const allDetails = document.querySelectorAll('.single-details');
    for (const details of allDetails) {
      details.addEventListener('toggle', function () {
        if (details.open) {
          for (const other of allDetails) if (other !== details) other.open = false;
        }
      });
    }
  });

  // expose functions for debugging if needed
  globalThis.loadFileList = loadFileList;
  globalThis.loadFileIntoEditor = loadFileIntoEditor;
  globalThis.saveFile = saveFile;
  globalThis.saveSQLFiles = saveSQLFiles;
})();

// random kommentare

// um mal zu schauen, ob das so geht