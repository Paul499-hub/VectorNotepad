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


// --- Notes
// datasets
// documentMetaEl.dataset.noteId // <-- workspace's note id dataset (single only)
// note_row.querySelector(".note-meta").dataset.noteId  // <-- note row's dataset (sidebar / one per note)
// ---- Important: anything that changes noteId must first check if saving is in progress, and avoid changing it during save using:
// if (isSaving) return // loading files is in progress


//"/get_note_attachment_metadata/{note_id}"
//"/get_file/{file_id}"


// Files cache
const pending_files = []
// Notes cache
const notes_by_id = new Map() // id => {"id":..., "score":..., "text":..., "preview":..., "html_md":... }
// Last search type - sql or vector - one uses scores and another doesn't
let lastSearchUsedScores = false
// Saving state (dont let swap notes while saving so noteId doesn't change)
let isSaving = false
// stored attachment variable (for discard reverts) (counts how many attachments are fetched from db)
let storedAttachmentCountCache 

// Attach files button
attachFileBtnEl.addEventListener("click", ()=>{
    attachFileInputEl.click()
})
attachFileInputEl.addEventListener("change", async ()=>{
    for (const file of attachFileInputEl.files) {
        pending_files.push(file)
        // Clone attachment element
        const attachment_fragment = attachmentBtnTemplate.content.cloneNode(true)
        const link = attachment_fragment.querySelector(".file-link")
        const url = URL.createObjectURL(file)
        // Add download & href
        link.href = url
        link.download = file.name
        // replace text content on span & small
        attachment_fragment.querySelector("span").textContent = file.name 
        attachment_fragment.querySelector("small").textContent = format_file_size(file.size) 
        // Add cloned element
        fileListEl.appendChild(attachment_fragment);
    }
    console.log("Pending attachments:", pending_files)
    if (pending_files.length > 0){
        fileListEl.querySelector(".empty-files").hidden = true
        unHideEdit()
    }
    attachmentCountEl.textContent = `STORED ATTACHMENTS / ${pending_files.length}`
    // Clear value for seperate file additions
    attachFileInputEl.value = ""
    // TODO: no removal ? 
})
// change text to `all notes` in both labels (breadcrumb & list heading)
allNotesFilterBtnEl.addEventListener("click", ()=>{
    allNotesFilterBtnEl.setAttribute("aria-pressed", "true")
    favouritesFilterBtnEl.setAttribute("aria-pressed", "false")
    breadcrumbLabelEl.textContent = "All notes"
    noteListLabelEl.textContent = "ALL NOTES"
})
// change text to `favourites` in both labels (breadcrumb & list heading)
favouritesFilterBtnEl.addEventListener("click", ()=>{
    favouritesFilterBtnEl.setAttribute("aria-pressed", "true")
    allNotesFilterBtnEl.setAttribute("aria-pressed", "false")
    breadcrumbLabelEl.textContent = "Favourites"
    noteListLabelEl.textContent = "FAVOURITES"
})

// Vector search button
vectorSearchBtnEl.addEventListener("click", vectorSearchNote)
// SQL search button
SQLSearchBtnEl.addEventListener("click", searchNoteSQL)
// Edit note btn
editNoteBtnEl.addEventListener("click", ()=>{
    unHideEdit()
    // Prefill edit with text of this note OR existing draft already
    const noteId = documentMetaEl.dataset.noteId
    if (noteId !== undefined){
        const currentNoteData = notes_by_id.get(Number(noteId))
        // find text input target and swap with notedatas text
        editorInputEl.value = currentNoteData.text
    }
})
// Save an edit btn | Save new note btn
saveNoteBtnEl.addEventListener("click", async ()=> {
    // disable save and edit
    if (isSaving) return
    isSaving = true
    run_animation(libraryEl, "loading")
    attachFileBtnEl.disabled = true
    attachFileInputEl.disabled = true
    saveNoteBtnEl.disabled = true
    try {
        // Get noteId
        let noteId = documentMetaEl.dataset.noteId
        const noteData = notes_by_id.get(Number(noteId))
        if (noteId === undefined) { // <- new note
            const response = await fetch( "/storage/save_note", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"text":editorInputEl.value})
                }
            );
            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || "Request failed");
                return;
            }
            const data = await response.json(); // {"id":..., "text":..., "html_md":...}
            // Add new note to in-memory notes_by_id
            notes_by_id.set(Number(data.id), data)
            // Display new note
            noteId = data.id
        }
        else { // <- note exists already
            // Send update request to backend
            const response = await fetch("/storage/update_note", {
                method: "PATCH",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ "id": noteId, "text": editorInputEl.value })
            });
            if (!response.ok){
                const err = await response.json();
                alert(err.detail || "Update failed");
                return;
            }
            const result = await response.json(); // { "updated_id":..., "old_text":..., new_text:..., new_html_md:... }
            // Update current note in notes_by_id
            noteData.html_md = result.new_html_md
            noteData.text = result.new_text
        }
        // Try uploading files (applies to both existing notes + new note)
        try {
            await upload_pending_files(noteId)
            // Display new note
            await swap_main_note(noteId)
            run_animation(noteDocumentEl, "reveal")
            HideEdit() 
            // Refresh the list
            fill_note_library(notes_by_id, lastSearchUsedScores)
        } catch (error) {
            console.error(error)
            alert("Note saved, but attachments failed. Click Save to retry.")
        }
    } catch (error) {
        console.error(error)
        alert("Could not complete the save. Check the console for details.")
    } finally {
        // Flip is saving check - allow notes to be clicked again
        isSaving = false
        stop_infinite_animation(libraryEl, "loading")
        // enable save and edit after upload
        attachFileBtnEl.disabled = false
        attachFileInputEl.disabled = false
        saveNoteBtnEl.disabled = false
    }
})
// Discard edits btn
discardEditsBtnEl.addEventListener("click", ()=>{
    if (isSaving) return // loading files is in progress
    // Clear attachments (only new)
    pending_files.length = 0
    let idx = 0 
    for (const link of fileListEl.querySelectorAll(".file-link")){
        idx = idx + 1
        console.log(idx)
        if (idx > storedAttachmentCountCache){
            URL.revokeObjectURL(link.href)
            link.remove()
        } 
    }
    attachmentCountEl.textContent = `STORED ATTACHMENTS / ${storedAttachmentCountCache}`  
    // Load show markdown of this specific note
    HideEdit()
    // Case discarding new note
    if (documentMetaEl.dataset.noteId === undefined){
        emptyNoteState()
    }
})
// New note btn
newNoteBtnEl.addEventListener("click", ()=>{
    if (isSaving) return
    clear_pending_attachments()
    delete documentMetaEl.dataset.noteId
    editorInputEl.value = ""
    unHideEdit()
})
// Delete note btn
deleteNoteBtnEl.addEventListener("click", async ()=>{
    if (isSaving) return
    const noteId = noteDocumentEl.querySelector("#document-meta").dataset.noteId
    if (noteId !== undefined){
        delete documentMetaEl.dataset.noteId
        const response = await fetch(`/storage/del/${noteId}`, {
            method: "DELETE",
        });
        if(!response.ok){
            const err = await response.json();
            alert(err.detail || "Delete failed");
            return;
        }
        const result = await response.json(); 
        //unHideEdit()
        emptyNoteState() // clear dataset and note display
        HideEdit()
        notes_by_id.delete(Number(noteId))
        // Refresh the list
        fill_note_library(notes_by_id, lastSearchUsedScores)
    }
})

// --------------------- FUNCTIONS
function clear_pending_attachments(resetStoredAttachmentCountCache = true){
    pending_files.length = 0
    for (const link of fileListEl.querySelectorAll(".file-link")){
        URL.revokeObjectURL(link.href)
        link.remove()
    }
    if (resetStoredAttachmentCountCache === true){
        storedAttachmentCountCache = 0
    }
    attachmentCountEl.textContent = `STORED ATTACHMENTS / ${storedAttachmentCountCache}`    
}
// Toggle between individual `active` note under `library` section of ui
async function add_notes_listeners(){
    const note_rows = document.querySelectorAll("#note-list .note-row")
    for (const note_row of note_rows) {
        note_row.addEventListener("click", async ()=>{
            // Do not switch if saving is still happening
            if (isSaving) return
            // Set all notes to aria-current false
            for (const note of note_rows) {
                note.setAttribute("aria-current", "false")
            }
            // Set currently active one to true only
            note_row.setAttribute("aria-current", "true")
            // Swap main note
            const noteId = Number(note_row.querySelector(".note-meta").dataset.noteId) // reading dataset returns str
            // Clear pending upload files
            clear_pending_attachments()
            // Show updated note
            await swap_main_note(noteId)
            HideEdit()
        })
    }
}
// Vector search
async function vectorSearchNote(){
    if (isSaving) return // loading files is in progress
    // Read search text 
    const text = searchInputEl.value.trim();
    // Loading animation
    run_animation(libraryEl, "loading")

    const resp = await fetch("/storage/similarity_search", {
        method: "POST",
        headers: {"Content-Type": "application/json"}, //application/x-www-form-urlencoded
        body: JSON.stringify({"text": text, "point_limit": 20})
    })
    if (!resp.ok){
        alert("Search failed")
        return
    }
    lastSearchUsedScores = true
    stop_infinite_animation(libraryEl, "loading")
    const resp_json = await resp.json()
    emptyNoteState()
    HideEdit()
    // [{"id":..., "score":..., "text":..., "preview":..., "html_md":... },...]
    // Cache each note under it's SQLite ID
    notes_by_id.clear()
    for (const note of resp_json){
        notes_by_id.set(note.id, note)
    }
    // notes_by_id [{117 -> {...}}]
    fill_note_library(notes_by_id, lastSearchUsedScores)
}
// Sql search
async function searchNoteSQL(){
    if (isSaving) return // loading files is in progress
    // Read search text 
    const text = searchInputEl.value.trim();
    if (!text){
        alert("Note text is empty!");
        return;
    }
    // Loading animation
    run_animation(libraryEl, "loading")
    const resp = await fetch("/sqlite/get", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({"text":text})
    })
    if (!resp.ok){
        alert("Search failed")
        return
    }
    lastSearchUsedScores = false
    stop_infinite_animation(libraryEl, "loading")
    const resp_json = await resp.json()
    emptyNoteState()
    HideEdit()
    // Cache each note under it's SQLite ID
    notes_by_id.clear()
    for (const note of resp_json){
        notes_by_id.set(note.id, note)
    }
    fill_note_library(notes_by_id, lastSearchUsedScores)
}
// Un-hide note text editor window
function unHideEdit(){
    // hide card-content (markdown) 
    mainNoteContentEl.hidden = true
    // un-hide edit bar (top) & editor window
    editBarEl.hidden = false
    editorInputEl.hidden = false
    // hide edit button - show save
    saveNoteBtnEl.hidden = false
    editNoteBtnEl.hidden = true
}

function editToSaveBtn(){
    // hide edit button - show save
    saveNoteBtnEl.hidden = false
    editNoteBtnEl.hidden = true
}


// Hide editor window and show note markdown
function HideEdit(){
    // show card-content (markdown) 
    mainNoteContentEl.hidden = false
    // hide edit bar (top) & editor window
    editBarEl.hidden = true
    editorInputEl.hidden = true
    // show edit button - hide save
    saveNoteBtnEl.hidden = true
    editNoteBtnEl.hidden = false
}
function emptyNoteState(){
    clear_pending_attachments()
    delete documentMetaEl.dataset.noteId
    editorInputEl.value = ""
    mainNoteContentEl.innerHTML = ""
    docReferenceEl.textContent = `ID / null`
}


function format_file_size(bytes){
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB`
    if (bytes < 1024 ** 3) return `${(bytes / (1024**2)).toFixed(1)} MiB`
    return `${(bytes / 1024 ** 3).toFixed(1)} GiB`
}

/**
 * 
 * @param {number} noteId 
 */
async function swap_main_note(noteId){
    // Gather data from notes_by_id for this noteId
    const selectedNoteData = notes_by_id.get(Number(noteId))
    // Swap html_md
    mainNoteContentEl.innerHTML = selectedNoteData.html_md
    // Swap note id (visual + dataset)
    docReferenceEl.textContent = `ID / ${noteId}`
    noteDocumentEl.querySelector("#document-meta").dataset.noteId = noteId
    // Reveal animation 
    run_animation(noteDocumentEl, "reveal")
    // Fetch note's attachments
    const resp = await fetch(`/sqlite/get_note_attachment_metadata/${noteId}`, {
        method: "GET",
    })
    if (!resp.ok) {
        const err = await resp.json()
        throw new Error(
            typeof err.detail === "string"
                ? err.detail
                : "Attachment upload failed"
        )
    }
    const data = await resp.json()
    storedAttachmentCountCache = data.length
    attachmentCountEl.textContent = `STORED ATTACHMENTS / ${storedAttachmentCountCache}`
    for (const d of data){ // Show attachments
        // file = {"id":..., "filename":..., content_type:..., size_bytes:...,}
        // Clone attachment element
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
    if (storedAttachmentCountCache === undefined || Number(storedAttachmentCountCache) < 1){
        fileListEl.querySelector(".empty-files").hidden = false
    } else {
        fileListEl.querySelector(".empty-files").hidden = true
    }
    attachmentCountEl.textContent = `STORED ATTACHMENTS / ${storedAttachmentCountCache}`
}

/**
 * 
 * @param {Map<number, Object>} notes_by_id
 * @param {boolean} show_score 
 */
function fill_note_library(notes_by_id, show_score){
    const noteCount = notes_by_id.size
    listHeadingEl.querySelector("#note-count").textContent = noteCount
    // Clear current note List
    noteListEl.innerHTML = ""
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
        if (show_score == true){
            if (note.score !== undefined){
                fragment.querySelector(".row-score").textContent = `sim ${note.score.toFixed(4)}`
            }   
        }
        else {
            fragment.querySelector(".row-score").textContent = ``
        }
        
        // Append template
        noteListEl.appendChild(fragment);
    }
    add_notes_listeners()
}

function remove_md_markers(text){
    return text.replace(/^#{1,6}\s+/, "")
}

function run_animation(targetEl, animation_class) {
    targetEl.classList.remove(animation_class)
    void targetEl.offsetWidth // force layout recalculation
    targetEl.classList.add(animation_class)
}
function stop_infinite_animation(targetEl, animation_class){
    targetEl.classList.remove(animation_class)
    void targetEl.offsetWidth // force layout recalculation
}

async function upload_pending_files(noteId) {
    if (pending_files.length === 0) return
    // Prepare Form for upload
    const formData = new FormData()
    formData.append("note_id", noteId)
    for (const file of pending_files){
        formData.append("files", file)
    }
    // Upload request
    const response = await fetch("/storage/store_files", {
        method: "POST",
        body: formData
    })
    // Validate response
    if (!response.ok) {
        const err = await response.json()
        throw new Error(
            typeof err.detail === "string"
                ? err.detail
                : "Attachment upload failed"
        )
    }
    // Json unpack response
    const data = await response.json()
    console.log("file data:", data) 
    // Remove successfully uploaded files
    clear_pending_attachments()
}
