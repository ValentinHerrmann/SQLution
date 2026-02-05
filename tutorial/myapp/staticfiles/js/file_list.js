// File list management for SQL IDE
// Handles file explorer, file operations (create, delete, rename), and file loading

let filenameOnLoad = "";
let contentOnLoad = "";

/**
 * Creates a button for the file list with specified styling and click handler
 * @param {string} title - Button title/tooltip
 * @param {string} color - CSS color for the button
 * @param {string} f - Filename
 * @param {string} icon - Font Awesome icon class
 * @param {Function} onclick - Click event handler
 * @returns {HTMLButtonElement} Configured button element
 */
function createBtnFilelistInline(title, color, f, icon, onclick) {
    let btn = document.createElement('button');
    btn.type = 'button';
    btn.title = title;
    btn.innerHTML = `<i class="${icon}" aria-hidden="true"></i>`;
    btn.style.marginLeft = '0px';
    btn.style.background = 'transparent';
    btn.style.border = 'none';
    btn.style.color = color;
    btn.style.cursor = 'pointer';
    btn.style.display = 'none';
    btn.addEventListener('click', async (e) => onclick(e, f));
    return btn;
}

/**
 * Handles delete button click event
 * @param {Event} e - Click event
 * @param {string} f - Filename to delete
 */
async function on_delBtn_click(e, f) {
    e.stopPropagation();
    const ok = await globalThis.showConfirmDialog(
        `Datei "${f}" wirklich löschen?`,
        "fas fa-trash",
        "var(--accent-danger)"
    );
    if (ok) {
        await deleteFile(f);
    }
}

/**
 * Handles rename button click event
 * @param {Event} e - Click event
 * @param {string} f - Filename to rename
 */
async function on_rnBtn_click(e, f) {
    e.stopPropagation();
    const ok = await globalThis.showConfirmDialog(
        `Datei "${f}" wirklich umbenennen?`,
        "far fa-edit"
    );
    if (ok) {
        let sql = '';
        const editor = globalThis.sqlAceEditor;
        if (editor) {
            sql = editor.getValue();
        }
        if (await addSQLFileDialog(sql)) {
            await deleteFile(f);
        }
    }
}

/**
 * Creates a delete button for a file
 * @param {string} f - Filename
 * @returns {HTMLButtonElement} Delete button
 */
function createDelBtn(f) {
    return createBtnFilelistInline('Löschen', 'var(--text-danger)', f, 'fas fa-trash', on_delBtn_click);
}

/**
 * Creates a rename button for a file
 * @param {string} f - Filename
 * @returns {HTMLButtonElement} Rename button
 */
function createRnBtn(f) {
    return createBtnFilelistInline('Umbenennen', 'var(--text-warning)', f, 'fas fa-edit', on_rnBtn_click);
}

/**
 * Deletes a SQL file from the server
 * @param {string} f - Filename to delete
 */
async function deleteFile(f) {
    try {
        const base = f.replace(/\.sql$/i, '');
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const uri = `/api/sql/${encodeURIComponent(base)}.sql`;
        const body = {
            method: 'DELETE',
            headers: csrftoken ? { 'X-CSRFToken': csrftoken } : {}
        }

        fetch(uri, body)
            .then((resp) => {
                if (resp.ok) {
                    // if deleted file was open, clear editor
                    if (filenameOnLoad === f) {
                        const editor = globalThis.sqlAceEditor;
                        if (editor) editor.setValue('', -1);
                        filenameOnLoad = '';
                        contentOnLoad = '';
                    }
                    loadFileList();
                } else {
                    showAlertDialog("Fehler beim Löschen der SQL Datei.", "fas fa-exclamation-triangle", "var(--accent-danger)");
                }
            });
    }
    catch (err) {
        console.error('Delete error', err);
        alert('Fehler beim Löschen der Datei.');
    }
}

/**
 * Creates a list item element for a file
 * @param {string} f - Filename
 * @returns {HTMLLIElement} List item element
 */
function fileList_createListElement(f) {
    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.justifyContent = 'space-between';
    li.style.alignItems = 'center';
    li.style.padding = '10px';
    li.style.paddingRight = '2px';
    li.style.cursor = 'pointer';
    li.style.borderBottom = '1px solid var(--border)';
    li.style.borderRadius = '4px';
    li.style.marginBottom = '0px';

    const nameSpan = document.createElement('span');
    nameSpan.textContent = f;
    nameSpan.style.flex = '1 1 auto';

    li.addEventListener('click', () => loadFileIntoEditor(f, li));
    li.appendChild(nameSpan);

    return li;
}

/**
 * Creates button container with delete and rename buttons
 * @param {string} f - Filename
 * @returns {HTMLDivElement} Button container
 */
function fileList_createBtns(f) {
    const btn_li = document.createElement('div');
    btn_li.style.display = 'flex';
    btn_li.style.flexDirection = 'column';
    btn_li.style.gap = '1px';
    btn_li.style.alignItems = 'center';

    const delBtn = createDelBtn(f);
    const rnBtn = createRnBtn(f);
    if (rnBtn) {
        btn_li.appendChild(rnBtn);
    }
    if (delBtn) {
        btn_li.appendChild(delBtn);
    }
    return btn_li;
}

/**
 * Prepares the file list container and shows loading state
 * @returns {HTMLUListElement} File list container element
 */
function fileList_prepareOuterScope() {
    const ul = document.getElementById('file-list');
    if (ul) {
        ul.innerHTML = '<li style="padding:0px; color:var(--text-secondary);">Lade Dateien…</li>';
    }
    return ul;
}

/**
 * Fetches file list data from the server
 * @returns {Promise<string[]>} Array of filenames
 */
async function fileList_loadData() {
    const resp = await fetch('/api/sql/list');
    if (!resp.ok) {
        throw new Error('Could not load file list');
    }
    const data = await resp.json();
    let files = data.files || [];
    files.unshift('Playground');
    return files;
}

/**
 * Loads and displays the file list in the explorer
 */
async function loadFileList() {
    const ul = fileList_prepareOuterScope();
    if (!ul) {
        throw new Error('Could not load file list');
    }
    try {
        const files = await fileList_loadData();
        if (files.length === 0) {
            ul.innerHTML = '<li style="padding:0.8rem; color:var(--text-secondary);">Keine SQL-Dateien gefunden.</li>';
            return;
        }

        ul.innerHTML = '';
        let firstLi = null;
        let idx = 0;
        for (const f of files) {
            const li = fileList_createListElement(f);

            if (f !== 'Playground') {
                const btn_li = fileList_createBtns(f);
                li.appendChild(btn_li);
            }
            ul.appendChild(li);
            if (idx === 0) {
                firstLi = li;
            }
            idx++;
        }

        if (firstLi) {
            await loadFileIntoEditor(files[0], firstLi);
        }
    } catch (err) {
        ul.innerHTML = '<li style="padding:0.8rem; color:var(--text-danger);">Fehler beim Laden der Dateien.</li>';
        console.error(err);
    }
}

/**
 * Saves a SQL file to the server
 * @param {string} filename - Name of the file to save
 * @param {string} content - SQL content to save
 * @returns {Promise<boolean>} True if save was successful
 */
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
            showAlertDialog(`Datei "${filename}" erfolgreich gespeichert.`, "fas fa-check-circle", "var(--accent-success)");
            return true;
        } else {
            console.error("Fehler beim Speichern der SQL Datei.", resp.status, resp.statusText);
            showAlertDialog("Fehler beim Speichern der SQL Datei.", "fas fa-exclamation-triangle", "var(--accent-danger)");
            return false;
        }
    } catch (err) {
        console.error('Error saving file:', err);
        showAlertDialog("Fehler beim Speichern der SQL Datei.", "fas fa-exclamation-triangle", "var(--accent-danger)");
        return false;
    }
}

/**
 * Saves the currently open file in the editor
 * @returns {Promise<boolean>} True if save was successful
 */
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
    if (filenameOnLoad === 'Playground') {
        showAlertDialog("Der Playground kann nicht gespeichert werden. Bitte erstelle eine neue SQL-Datei über das '+'-Symbol im Dateiexplorer.", "fas fa-exclamation-triangle");
        return false;
    }

    console.log("Content to save: " + content);
    console.log("Filename to save: " + filenameOnLoad);
    return await saveFile(filenameOnLoad, content);
}

/**
 * Loads a file into the editor
 * @param {string} filename - Name of the file to load
 * @param {HTMLLIElement} liElement - List item element that was clicked
 */
async function loadFileIntoEditor(filename, liElement) {
    try {
        // restore editor height when opening a file (remove result view)
        if (typeof restoreEditorHeight === 'function') {
            restoreEditorHeight();
        }

        const editor = globalThis.sqlAceEditor;
        if (!editor) throw new Error('Editor not initialized');

        if (editor.getValue() !== contentOnLoad) {
            if (filenameOnLoad === 'Playground') {
                sessionStorage.setItem('sql_playground', editor.getValue());
            }
            else {
                const confirmed = await globalThis.showConfirmDialog(
                    "Änderungen speichern? Wenn nicht gespeichert wird, gehen diese verloren.",
                    "fas fa-save"
                );
                if (confirmed) {
                    if (filenameOnLoad !== 'Playground') {
                        let success = await saveCurrentFile();
                        console.log("Save success: " + success);
                        if (!success) {
                            showAlertDialog("Speichern der Datei fehlgeschlagen. Abbruch des Ladevorgangs.", "fas fa-exclamation-triangle");
                            return;
                        }
                    }
                }
            }
        }

        // highlight selection and show delete button only for selected
        // hide all buttons on all list items
        for (const el of document.querySelectorAll('#file-list li')) {
            el.style.background = '';
            const buttons = el.querySelectorAll('button');
            for (const b of buttons) {
                b.style.display = 'none';
            }
        }
        // show all buttons for the selected list item
        if (liElement) {
            liElement.style.background = 'var(--text-muted)';
            const buttons = liElement.querySelectorAll('button');
            for (const b of buttons) {
                b.style.display = 'inline-block';
            }
        }
        if (filename === 'Playground') {
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
            editor.setValue(content, -1);
            contentOnLoad = content;
            filenameOnLoad = filename;
        }
    } catch (err) {
        console.error(err);
        showAlertDialog('Fehler beim Laden der Datei. Siehe Konsole.', "fas fa-exclamation-triangle");
    }
}

/**
 * Shows dialog to create a new SQL file
 * @param {string} sql - Initial SQL content for the new file
 * @returns {Promise<boolean>} True if file was created successfully
 */
async function addSQLFileDialog(sql = '') {
    let filename = prompt('Dateiname');
    if (!filename) return false;
    if (!filename.toLowerCase().endsWith('.sql')) filename += '.sql';
    let ret = false
    try {
        const base = filename.replace(/\.sql$/i, '');
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const url = `/api/sql/${encodeURIComponent(base)}.sql`;
        const headers = { "Content-Type": "application/json" };
        if (csrftoken) headers['X-CSRFToken'] = csrftoken;
        const body = JSON.stringify({ sql: sql });

        const resp = await fetch(url, {
            method: "PUT",
            headers: headers,
            body: body
        });

        if (resp.ok) {
            console.debug("File created successfully: " + filename);
            ret = true;
        } else {
            console.error("Fehler beim Erstellen der SQL Datei.", resp.status, resp.statusText);
            showAlertDialog("Fehler beim Erstellen der SQL Datei.", "fas fa-exclamation-triangle");
        }
    } catch (err) {
        console.error('Error creating file:', err);
        showAlertDialog("Fehler beim Erstellen der SQL Datei.", "fas fa-exclamation-triangle");
    }
    await loadFileList();
    return ret;
}

/**
 * Saves all SQL files from the IDE
 */
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

// Expose API for use in other modules
globalThis.loadFileList = loadFileList;
globalThis.loadFileIntoEditor = loadFileIntoEditor;
globalThis.saveFile = saveFile;
globalThis.saveSQLFiles = saveSQLFiles;
globalThis.saveCurrentFile = saveCurrentFile;
globalThis.addSQLFileDialog = addSQLFileDialog;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadFileList,
        loadFileIntoEditor,
        saveFile,
        saveCurrentFile,
        addSQLFileDialog,
        saveSQLFiles,
        deleteFile,
        filenameOnLoad,
        contentOnLoad
    };
}
