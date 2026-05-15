// SQL IDE client-side logic: Ace initialization and SQL execution
// File list functionality is in file_list.js
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

        // Update editor colors when theme changes
        updateEditorColors();
    } catch (err) {
        console.error('Error initializing ACE editor:', err);
    }
}

function updateEditorColors() {
    const editor = globalThis.sqlAceEditor;
    if (!editor) return;

    // Force refresh of editor rendering
    editor.renderer.updateFull();
}

// File list functionality moved to file_list.js

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
    if(columns.length > 0) {
        resultsContainer.style.padding = '10px';
    }
    else {
        resultsContainer.style.padding = '0px';
    }

    const table = document.createElement('table');
    table.setAttribute('border', '1');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';

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
    var sql = editor.getValue();
    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const headers = { 'Content-Type': 'application/json' };
        if (csrftoken) {
            headers['X-CSRFToken'] = csrftoken;
        }
        const resp = await fetch('/api/sql/resolve_subqueries', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ sql: sql })
        });
        if (resp.ok) {
            sql = await resp.text();    
        } else {
        console.error(`Error resolving subqueries: `, resp.status);
        }
    } catch (e) {
        console.error(`Error resolving subqueries:`, e);
    }

    const proceed = await warnIfDDL(sql);
    if(!proceed) {
        return;
    }

    const successContainer = document.getElementById('sql-success');
    const resultsContainer = document.getElementById('sql-results');
    if (!resultsContainer) return;

    // Hide success container at the start
    if (successContainer) {
        successContainer.style.display = 'none';
        successContainer.innerHTML = '';
    }

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
            successContainer.style.display = 'block';
            successContainer.innerHTML = `<div style="padding:2px;color:var(--text-danger);"><p>Fehler beim Ausführen der Abfrage:</p> ${escapeHtml(errorMsg)}</div>`;
            console.error('Run SQL HTTP error', resp.status, errorMsg);
            setEditorHalf();
            return;
        }
        const data = await resp.json();
        if (data.error) {
            successContainer.style.display = 'block';
            successContainer.innerHTML = `<div style="padding:2px;color:var(--text-danger);">Fehler: ${escapeHtml(data.error)}</div>`;
            setEditorHalf();
            return;
        }
        const columns = data.columns || [];
        const rows = data.result || [];
        renderResultsTable(columns, rows, resultsContainer);
        setEditorHalf();
        successContainer.style.display = 'block';
        successContainer.innerHTML = `<div style="padding:2px;color:var(--text-success);"><i class="fas fa-check-circle" aria-hidden="true" style="margin-right:6px;"></i>Abfrage erfolgreich ausgeführt.</div>`;
    } catch (err) {
        console.error('Run SQL error', err);
        successContainer.style.display = 'block';
        successContainer.innerHTML = `<div style="padding:2px;color:var(--text-danger);"><p>Fehler beim Ausführen der Abfrage:</p> ${err}</div>`;
        setEditorHalf();
    }
}

// Adjust editor height to half the viewport and trigger Ace resize
function setEditorHalf() {
    try {
        const editorElem = document.getElementById('editor');
        if (!editorElem) return;
        if (prevEditorHeight === null) prevEditorHeight = editorElem.style.height || globalThis.getComputedStyle(editorElem).height || '';
        editorElem.style.height = '85%';
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
    if (typeof query !== 'string') {
        return false;
    }
    const ddlPattern = /(^|;)\s*(CREATE|ALTER|DROP|TRUNCATE|RENAME)\b/i;
    return ddlPattern.test(query);
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
    if (saveBtn) {
        saveBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            await saveCurrentFile();
        });
    }

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

// Listen for theme changes
globalThis.addEventListener('themeChanged', function() {
    updateEditorColors();
});

