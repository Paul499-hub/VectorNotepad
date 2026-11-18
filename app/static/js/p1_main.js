
//  Toggle between `all notes` | `favourites` in ui 
const allNotesFilterBtnEl = document.getElementById("all-notes")
const favouritesFilterBtnEl = document.getElementById("favourites")
const breadcrumbLabelEl = document.getElementById("breadcrumb-label")
const noteListLabelEl = document.getElementById("note-list-label")
const vectorSearchBtnEl = document.getElementById("vector")
const SQLSearchBtnEl = document.getElementById("keyword")
const searchInputEl = document.getElementById("search")
const noteTemplate = document.getElementById("library-note-template")
const noteListEl = document.getElementById("note-list")
const mainNoteContentEl = document.getElementById("card-content")
const listHeadingEl = document.querySelector(".list-heading")
const noteDocumentEl = document.getElementById("document")
const libraryEl = document.getElementById("library")
const editNoteBtnEl = document.getElementById("edit")
const saveNoteBtnEl = document.getElementById("save")
const editBarEl = document.getElementById("edit-bar")
const editorInputEl = document.getElementById("editor")
const discardEditsBtnEl = document.getElementById("discard")
const documentMetaEl = document.getElementById("document-meta")
const saveEditBtnEl = document.getElementById("save")
const newNoteBtnEl = document.getElementById("new-note-btn")
const deleteNoteBtnEl = document.getElementById("delete")

// datasets
// note_row.querySelector(".note-meta").dataset.noteId
// noteDocumentEl.querySelector("#document-meta").dataset.noteId = noteId

// Notes cache
const notes_by_id = new Map() // id => {"id":..., "score":..., "text":..., "preview":..., "html_md":... }
// Last search type - sql or vector - one uses scores and another doesn't
let lastSearchUsedScores = false
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
    const currentNoteData = notes_by_id.get(Number(noteId))
    //notes_by_id.get(noteId)
    // find text input target and swap with notedatas text
    editorInputEl.value = currentNoteData.text
})
// Save an edit btn
saveEditBtnEl.addEventListener("click", async ()=> {
    // Get noteId
    const noteId = noteDocumentEl.querySelector("#document-meta").dataset.noteId
    const noteData = notes_by_id.get(Number(noteId))
    if (documentMetaEl.dataset.noteId == -1) {
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
        // Display new note
        mainNoteContentEl.innerHTML = data.html_md
        noteDocumentEl.querySelector("#document-reference").textContent = `ID / ${data.id}`
        noteDocumentEl.querySelector("#document-meta").dataset.noteId = data.id
        run_animation(noteDocumentEl, "reveal")
        HideEdit() 
        // Refresh the list
        fill_note_library(notes_by_id, lastSearchUsedScores)
    }
    else {
        // Send update request to backend
        const response = await fetch("/storage/update_note", {
            method: "PATCH",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({"id":noteId, "text":editorInputEl.value })
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
        // Display new note
        swap_main_note(noteId)
        HideEdit() 
        // Refresh the list
        fill_note_library(notes_by_id, lastSearchUsedScores)
    }

})
// Discard edits btn
discardEditsBtnEl.addEventListener("click", ()=>{
    // Load show markdown of this specific note
    HideEdit()
    // TODO: delete note draft in memory
})
// New note btn
newNoteBtnEl.addEventListener("click", ()=>{
    documentMetaEl.dataset.noteId = -1
    editorInputEl.value = ""
    unHideEdit()
})
// Delete note btn
deleteNoteBtnEl.addEventListener("click", async ()=>{
    noteId = noteDocumentEl.querySelector("#document-meta").dataset.noteId
    const response = await fetch(`/storage/del/${noteId}`, {
        method: "DELETE",
    });
    if(!response.ok){
        const err = await response.json();
        alert(err.detail || "Delete failed");
        return;
    }
    const result = await response.json(); 
    documentMetaEl.dataset.noteId = -1
    editorInputEl.value = ""
    unHideEdit()
    notes_by_id.delete(Number(noteId))
    // Refresh the list
    fill_note_library(notes_by_id, lastSearchUsedScores)
})

// Toggle between individual `active` note under `library` section of ui
function add_notes_listeners(){
    const note_rows = document.querySelectorAll("#note-list .note-row")
    for (const note_row of note_rows) {
        note_row.addEventListener("click", ()=>{
            // Set all notes to aria-current false
            for (const note of note_rows) {
                note.setAttribute("aria-current", "false")
            }
            // Set currently active one to true only
            note_row.setAttribute("aria-current", "true")
            // Swap main note
            const noteId = Number(note_row.querySelector(".note-meta").dataset.noteId) // reading dataset returns str
            swap_main_note(noteId)
            HideEdit()
        })
    }
}
// Vector search
async function vectorSearchNote(){
    // Read search text 
    const text = searchInputEl.value.trim();
    // Loading animation
    run_animation(libraryEl, "loading")
    // TODO - check if note text is empty
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


/**
 * 
 * @param {number} noteId 
 */
function swap_main_note(noteId){
    // Gather data from notes_by_id for this noteId
    const selectedNoteData = notes_by_id.get(Number(noteId))
    // Find main targets
    mainNoteContentEl.innerHTML = selectedNoteData.html_md
    // Swap note id
    noteDocumentEl.querySelector("#document-reference").textContent = `ID / ${noteId}`
    noteDocumentEl.querySelector("#document-meta").dataset.noteId = noteId
    // Reveal animation 
    run_animation(noteDocumentEl, "reveal")
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
            fragment.querySelector(".row-score").textContent = `sim ${note.score.toFixed(4)}`
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
