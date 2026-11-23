// -------- TEMPLATES ------------
const attachmentBtnTemplate = document.getElementById("stored-attachments-template")
const noteTemplate = document.getElementById("library-note-template")
// ~~~~~~~~~ BUTTONS ~~~~~~~~~~
const favouritesFilterBtnEl = document.getElementById("favourites")
const allNotesFilterBtnEl = document.getElementById("all-notes")
const discardEditsBtnEl = document.getElementById("discard")
const newNoteBtnEl = document.getElementById("new-note-btn")
const vectorSearchBtnEl = document.getElementById("vector")
const deleteNoteBtnEl = document.getElementById("delete")
const attachFileBtnEl = document.getElementById("attach")
const SQLSearchBtnEl = document.getElementById("keyword")
const editNoteBtnEl = document.getElementById("edit")
const saveNoteBtnEl = document.getElementById("save")
// ======== OTHER ===============
const attachmentCountEl = document.getElementById("attachment-count")
const breadcrumbLabelEl = document.getElementById("breadcrumb-label")
const docReferenceEl = document.getElementById("document-reference")
const noteListLabelEl = document.getElementById("note-list-label")
const mainNoteContentEl = document.getElementById("card-content")
const documentMetaEl = document.getElementById("document-meta")
const attachFileInputEl = document.getElementById("file-input")
const listHeadingEl = document.querySelector(".list-heading")
const noteDocumentEl = document.getElementById("document")
const searchInputEl = document.getElementById("search")
const noteListEl = document.getElementById("note-list")
const editorInputEl = document.getElementById("editor")
const fileListEl = document.getElementById("file-list")
const editBarEl = document.getElementById("edit-bar")
const libraryEl = document.getElementById("library")

// note ID is in memory variable
// pending attachments will have a new class so they can be targeted

// IMPORTANT > when creating new attachment > link.classList.add("pending")
let mainNoteId 
const pending_files = []
const notes_by_id = new Map() // id => {"id":..., "score":..., "reranked_score"..., "text":..., "html_md":... }
let isLoading = false
let originalAttachmentCountCache // stored attachment variable (for discard reverts) (counts how many attachments were fetched from db)
let lastSearchUsedScores = false
// ~~~~~~~~~~ UI 

function ui_read_search_bar_text(){
    return searchInputEl.value.trim();
}

/**
 * Restarts a CSS animation by removing and re-adding its class.
 *
 * @param {HTMLElement} targetEl - Element to animate.
 * @param {string} animation_class - CSS class containing the animation.
 * @returns {void}
 */
function ui_run_animation(targetEl, animation_class) {
    targetEl.classList.remove(animation_class)
    void targetEl.offsetWidth // Force layout recalculation before re-adding the class
    targetEl.classList.add(animation_class)
}

/**
 * Stops a CSS animation by removing its class.
 *
 * @param {HTMLElement} targetEl - Element whose animation should stop.
 * @param {string} animation_class - CSS class containing the animation.
 * @returns {void}
 */
function ui_stop_infinite_animation(targetEl, animation_class) {
    targetEl.classList.remove(animation_class)
}

/**
 * Clears the editor text, main note's html_md and displayed note id.
 * @returns {void}
 */
function ui_clear_main_note_elements() {
    editorInputEl.value = ""
    mainNoteContentEl.innerHTML = ""
    docReferenceEl.textContent = "ID / null"
}

/**
 * Removes attachment links matching the selector and releases temporary URLs.
 * @param {string} selector - CSS selector, e.g. ".file-link.pending" or ".file-link".
 * @returns {void}
 */
function ui_clear_attachments(selector){
    for (const link of fileListEl.querySelectorAll(selector)){
        if (link.href.startsWith("blob:")) { // ignore revoking of non `URL.createObjectURL()` temporary url's
            URL.revokeObjectURL(link.href)
        }
        link.remove()
    }
}

/**
 * Shows html_md element and Edit button.
 * Hides the editor, edit bar and Save button.
 * @returns {void}
 */
function ui_hide_main_note_edit_state(){
    // show card-content (markdown) & edit btn
    mainNoteContentEl.hidden = false
    editNoteBtnEl.hidden = false
    // hide edit bar (top) & editor window
    editBarEl.hidden = true
    editorInputEl.hidden = true
    saveNoteBtnEl.hidden = true
}

// Un-hide note text editor window
function ui_show_main_note_edit_state(){
    // hide card-content (markdown) | edit note btn
    mainNoteContentEl.hidden = true
    editNoteBtnEl.hidden = true
    // show edit bar (top) & editor window & save btn
    editBarEl.hidden = false
    editorInputEl.hidden = false
    saveNoteBtnEl.hidden = false
    
}



/**
 * Marks the given library row as current and deselects all other rows.
 * @param {HTMLElement} note_row - Note row to activate.
 * @param {NodeListOf<HTMLElement>} note_rows - All library note rows
 * @returns {void}
 */
function ui_make_note_active(note_row, note_rows){
    // Set all notes to aria-current false
    for (const note of note_rows) {
        note.setAttribute("aria-current", "false")
    }
    // Set currently active one to true only
    note_row.setAttribute("aria-current", "true")
}

/**
 * Changes main note's html_md and updates its displayed ID
 * @param {number} noteId - SQLite ID of the note
 * @param {string} html_md - Note data containing rendered HTML 'html_md'
 * @returns {void}
 */
function ui_swap_main_note_text(noteId, html_md){
    // Swap html_md
    mainNoteContentEl.innerHTML = html_md
    // Swap note id (visual + dataset)
    docReferenceEl.textContent = `ID / ${noteId}`
}

/**
 * Appends stored attachment link elements with filenames and formatted sizes.
 * @param {Array<{id: number, filename: string, content_type: string, size_bytes: number}>} data - Stored attachment metadata.
 * @returns {void}
 */
function ui_append_attachments(data){
    for (const d of data){ // d = {"id":..., "filename":..., content_type:..., size_bytes:...,}
        const attachment_fragment = attachmentBtnTemplate.content.cloneNode(true)
        const link = attachment_fragment.querySelector(".file-link")
        link.href = `/sqlite/get_file/${d.id}`
        //link.download = file.name
        // replace text content on span & small
        attachment_fragment.querySelector("span").textContent = d.filename 
        attachment_fragment.querySelector("small").textContent = format_file_size(d.size_bytes) 
        // Add cloned element
        fileListEl.appendChild(attachment_fragment);
    }
}


// -------- LISTENER FUNCTIONS

// Vector search
vectorSearchBtnEl.addEventListener("click", async ()=>{
    sql_vec_search(true)
})
// SQL search button
SQLSearchBtnEl.addEventListener("click", async ()=>{
    sql_vec_search(false)
})
// New note btn
newNoteBtnEl.addEventListener("click", ()=>{
    if (isLoading) return
    // Clear main note UI 
    ui_clear_main_note_elements()
    mainNoteId = undefined
    pending_files.length = 0 // clear pending files
    attachmentCountEl.textContent = `STORED ATTACHMENTS / 0` 
    ui_clear_attachments(".file-link") // Clear ALL attachments html
    originalAttachmentCountCache = 0
    fileListEl.querySelector(".empty-files").hidden = false // Show no attachments 
    const note_rows = document.querySelectorAll("#note-list .note-row")
    for (const note of note_rows) { // Set all notes to aria-current false (non-selected)
        note.setAttribute("aria-current", "false")
    }
    ui_show_main_note_edit_state()
})
// Attach file
attachFileBtnEl.addEventListener("click", ()=>{
    if (isLoading){return}
    attachFileInputEl.click()
})
attachFileInputEl.addEventListener("change", async ()=>{ // Attach file input
    for (const file of attachFileInputEl.files) {
        pending_files.push(file) // Store pending file in memory
        // Add template clone        
        const attachment_fragment = attachmentBtnTemplate.content.cloneNode(true)
        const link = attachment_fragment.querySelector(".file-link")
        link.classList.add("pending")
        link.href = URL.createObjectURL(file) // Create temp link for file
        // replace text content on span & small
        attachment_fragment.querySelector("span").textContent = file.name 
        attachment_fragment.querySelector("small").textContent = format_file_size(file.size) 
        // Add cloned element
        fileListEl.appendChild(attachment_fragment);
    }
    if (pending_files.length > 0){ // If more than 1 file was selected - open editor window
        fileListEl.querySelector(".empty-files").hidden = true
        // Prefill text if editor was hidden && if existing note selected
        if (editorInputEl.hidden && mainNoteId !== undefined){
            editorInputEl.value = notes_by_id.get(mainNoteId).text
        }
        ui_show_main_note_edit_state()
    }
    // Clear value for seperate file additions
    attachFileInputEl.value = ""
})
// Discard edits btn
discardEditsBtnEl.addEventListener("click", ()=>{
    if (isLoading) return
    // Clear attachments (only new)
    ui_clear_attachments(".file-link.pending")
    pending_files.length = 0
    ui_hide_main_note_edit_state()
    // Show no attachments or not
    if (originalAttachmentCountCache > 0){
        fileListEl.querySelector(".empty-files").hidden = true
    }else {
        fileListEl.querySelector(".empty-files").hidden = false
    }
    editorInputEl.value = "" // clear editor value
})
// Edit note btn
editNoteBtnEl.addEventListener("click", ()=>{
    if (isLoading) return
    ui_show_main_note_edit_state()
    if (mainNoteId !== undefined){
        editorInputEl.value = notes_by_id.get(Number(mainNoteId)).text
    }
})
// Save note btn
saveNoteBtnEl.addEventListener("click", async ()=> {
    if (isLoading) return
    isLoading = true
    editorInputEl.readOnly = true // Disable typing during saving
    ui_run_animation(libraryEl, "loading")
    try{
        let resp_json
        if (mainNoteId===undefined){ // <-- saving new note
            resp_json = await get_backend_json("/storage/save_note", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({"text":editorInputEl.value})
            })// {"id":..., "text":..., "html_md":...}
            // Add new note to in-memory notes_by_id
            notes_by_id.set(Number(resp_json.id), resp_json)
            mainNoteId = resp_json.id // new note gains ID
        } else { // <-- saving existing note
            resp_json = await get_backend_json("/storage/update_note", {
                method: "PATCH",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ "id": mainNoteId, "text": editorInputEl.value })
            }); // { "updated_id":..., "old_text":..., new_text:..., new_html_md:... }
            // Update current note in notes_by_id
            const noteData = notes_by_id.get(Number(mainNoteId))
            noteData.html_md = resp_json.new_html_md
            noteData.text = resp_json.new_text
        }
        // Try uploading files (applies to both existing notes & new note)
        try {
            await upload_pending_files(mainNoteId)
            // Remove successfully uploaded files from pending 
            const links = document.querySelectorAll(".file-link.pending")
            for (const link of links){
                link.classList.remove('pending')
            }
            // Update attachment counters
            if (originalAttachmentCountCache === undefined){
                originalAttachmentCountCache = links.length
            } else {
                originalAttachmentCountCache += links.length
            }
            attachmentCountEl.textContent = `STORED ATTACHMENTS / ${originalAttachmentCountCache}`
            pending_files.length = 0
            // replace main html_md , attachment counter, hide no attachments if attachments exist
            ui_swap_main_note_text(mainNoteId, resp_json.html_md ?? resp_json.new_html_md  )
            ui_hide_main_note_edit_state()
            // Refresh not library
            listHeadingEl.querySelector("#note-count").textContent = notes_by_id.size // Display updated note count
            noteListEl.innerHTML = "" // Clear current note list html
            fill_note_library(notes_by_id, lastSearchUsedScores)
        } catch (error) {
            console.error(error)
            alert("Note saved, but attachments failed. Click Save to retry.")
        }
    } catch {
        console.error(error)
        alert("Could not complete the save.")
    } finally {
        isLoading = false
        editorInputEl.readOnly = false
        ui_stop_infinite_animation(libraryEl, "loading")
    }
})
// Delete note btn
deleteNoteBtnEl.addEventListener("click", async ()=>{
    if (isLoading) return 
    if (mainNoteId === undefined) return
    isLoading = true
    const resp_json = await get_backend_json(`/storage/del/${mainNoteId}`, {
        method: "DELETE",
    });
    isLoading = false
    ui_clear_main_note_elements()
    ui_hide_main_note_edit_state()
    notes_by_id.delete(Number(mainNoteId))
    pending_files.length = 0 // clear pending files in memory
    attachmentCountEl.textContent = `STORED ATTACHMENTS / 0` 
    ui_clear_attachments(".file-link") // Clear ALL attachments html
    fileListEl.querySelector(".empty-files").hidden = false // 'No attachments'
    originalAttachmentCountCache = 0
    mainNoteId = undefined
    // Refresh note list
    listHeadingEl.querySelector("#note-count").textContent = notes_by_id.size // Display updated note count
    noteListEl.innerHTML = "" // Clear current note list html
    fill_note_library(notes_by_id, lastSearchUsedScores)
})






// Toggle between individual `active` note under `library` section of ui
async function add_notes_listeners(){
    const note_rows = document.querySelectorAll("#note-list .note-row")
    for (const note_row of note_rows) {
        note_row.addEventListener("click", async ()=>{
            if (isLoading) return // Do not switch if saving/loading is still happening
            ui_make_note_active(note_row, note_rows)

            const noteId = Number(note_row.querySelector(".note-meta").dataset.noteId) // Read clicked note id
            mainNoteId = noteId
        
            const selectedNoteData = notes_by_id.get(Number(noteId)) // Gather data from notes_by_id for this noteId
            ui_swap_main_note_text(noteId, selectedNoteData.html_md) // Swap visable html_md and note id 

            ui_hide_main_note_edit_state()

            ui_run_animation(noteDocumentEl, "reveal")

            ui_clear_attachments(".file-link") // Clear stored + pending attachments
            pending_files.length = 0 // clear pending files in memory
            
            isLoading = true
            try{
                const resp_json = await get_backend_json( // Fetch attachment metadata only
                    `/sqlite/get_note_attachment_metadata/${noteId}`, 
                    {method: "GET"}
                )// [{"id":..., "filename":..., content_type:..., size_bytes:...,}]
                originalAttachmentCountCache = resp_json.length
                attachmentCountEl.textContent = `STORED ATTACHMENTS / ${originalAttachmentCountCache}` // Update attachment count
                // Show "No attachments" text or not based on numAttachments
                if (originalAttachmentCountCache > 0){
                    fileListEl.querySelector(".empty-files").hidden = true
                }else {
                    fileListEl.querySelector(".empty-files").hidden = false
                } 
                ui_append_attachments(resp_json)
            } catch (error) {
                console.error(error)
                alert("Could not load attachments")
            } finally {
                isLoading = false
            }            
        })
    }
}


// --------- REQUESTS

/**
 * Fetches JSON from the backend; throws if the request fails.
 * @param {string} url
 * @param {RequestInit} options - Optional fetch settings.
 * @returns {Promise<any>}
 */
async function get_backend_json(url, options = {}) {
    const resp = await fetch(url, options)
    if (!resp.ok) {
        const error = await resp.json().catch(() => null)
        throw new Error(
            typeof error?.detail === "string"
                ? error.detail
                : `Request failed (${resp.status})`
        )
    }
    return await resp.json()
}

// ----------- OTHER

/**
 * 
 * @param {Map<number, Object>} notes_by_id - In memory notes to display in html
 * @param {boolean} show_score  - variable to determine if we show simmilarity scores or not
 */
function fill_note_library(notes_by_id, show_score){
    for (const [id, note] of notes_by_id){
        // Clone note template
        const fragment = noteTemplate.content.cloneNode(true)
        // Parse text into title / preview (after title)
        const lines = note.text.split('\n')
        const title = lines[0]
        const preview = lines.slice(1).join(" ").trim()
        // Update template
        fragment.querySelector(".note-title").textContent = remove_md_markers(title)
        fragment.querySelector(".note-preview").textContent = remove_md_markers(preview)
        fragment.querySelector(".note-meta").dataset.noteId = note.id 
        fragment.querySelector(".note-id").textContent = `ID / ${note.id}`
        // Show score
        if (show_score && note.score !== undefined){
            if (note.reranked_score !== undefined){
                fragment.querySelector(".row-score").textContent = `rank ${note.reranked_score.toFixed(4)}`
            }else {
                fragment.querySelector(".row-score").textContent = `sim ${note.score.toFixed(4)}`
            }
            
        } else {
            fragment.querySelector(".row-score").textContent = ``
        }
        // Append template
        noteListEl.appendChild(fragment);
    }
    add_notes_listeners()
}

/**
 * Searches notes using vector similarity or SQL keyword matching.
 * Clears the current selection and attachments, caches the results,
 * and rebuilds the library. Shows similarity scores only for vector search.
 * @param {boolean} is_vector - True for vector search; false for SQL search.
 * @returns {Promise<void>}
 */
async function sql_vec_search(is_vector){
    if (isLoading) {return}
    lastSearchUsedScores = is_vector
    const s_text = ui_read_search_bar_text()
    ui_run_animation(libraryEl, "loading")
    isLoading = true
    let resp_json
    if (is_vector) {
        resp_json = await get_backend_json("/storage/similarity_search", {
            method: "POST",
            headers: {"Content-Type": "application/json"}, //application/x-www-form-urlencoded
            body: JSON.stringify({"text": s_text, "point_limit": 50})
        }) // [{"id":..., "score":..., "reranked_score"..., "text":..., "html_md":... },...]
    } else {
        resp_json = await get_backend_json("/sqlite/get", {
            method: "POST",
            headers: {"Content-Type": "application/json"}, //application/x-www-form-urlencoded
            body: JSON.stringify({"text": s_text})
        }) // [{"id":..., "score":..., "text":..., "html_md":... },...]
    }
    isLoading = false
    ui_stop_infinite_animation(libraryEl, "loading")
    // Clear main note UI 
    ui_clear_main_note_elements()
    mainNoteId = undefined
    pending_files.length = 0 // clear pending files
    attachmentCountEl.textContent = `STORED ATTACHMENTS / 0` 
    ui_clear_attachments(".file-link") // Clear ALL attachments html
    originalAttachmentCountCache = 0
    fileListEl.querySelector(".empty-files").hidden = false // Show no attachments 
    ui_hide_main_note_edit_state()
    // Clear + cache each note under it's SQLite ID
    notes_by_id.clear()
    for (const r of resp_json){notes_by_id.set(r.id, r)}
    listHeadingEl.querySelector("#note-count").textContent = notes_by_id.size // Display updated note count
    noteListEl.innerHTML = "" // Clear current note list html
    fill_note_library(notes_by_id, is_vector) // Display in-memory notes with scores
}


/**
 * Removes a leading Markdown heading marker (# through ######) and its whitespace.
 * @param {string} text - Text to process.
 * @returns {string} Text without the leading heading marker, if present.
 */
function remove_md_markers(text) {
    return text.replace(/^#{1,6}\s+/, "")
}

/**
 * Formats a byte count as B, KiB, MiB or GiB.
 * Uses one decimal place for units larger than bytes.
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function format_file_size(bytes){
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB`
    if (bytes < 1024 ** 3) return `${(bytes / (1024**2)).toFixed(1)} MiB`
    return `${(bytes / 1024 ** 3).toFixed(1)} GiB`
}

async function upload_pending_files(noteId){
    if (pending_files.length === 0) return
    // Prepare Form for upload
    const formData = new FormData()
    formData.append("note_id", noteId)
    for (const file of pending_files){
        formData.append("files", file)
    }
    // Upload request
    const resp_json = await get_backend_json("/storage/store_files", {
        method: "POST",
        body: formData
    })
    return resp_json
}