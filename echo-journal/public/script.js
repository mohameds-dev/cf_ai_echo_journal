let state = 'Ready';
let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById('recordBtn');
const cancelBtn = document.getElementById('cancelBtn');
const journalWindow = document.getElementById('journal-window');

function checkEmptyState() {
    const hasEntries = journalWindow.querySelectorAll('.entry').length > 0;
    const existingPlaceholder = document.getElementById('empty-placeholder');

    if (!hasEntries && !existingPlaceholder) {
        const placeholder = document.createElement('div');
        placeholder.id = 'empty-placeholder';
        placeholder.innerHTML = `
            <div class="placeholder-content">
                <span class="icon">📝</span>
                <p>Whoa, it's empty in here.</p>
                <small>Click the record button and speak your thoughts so we can journal!</small>
            </div>
        `;
        journalWindow.appendChild(placeholder);
    } else if (hasEntries && existingPlaceholder) {
        existingPlaceholder.remove();
    }
}

function applyState(newState) {
    state = newState;
    console.log("Current State:", state);

    switch (state) {
        case 'Ready':
            recordBtn.innerText = "Record";
            recordBtn.disabled = false;
            cancelBtn.classList.add('hidden');
            break;
        case 'Recording':
            recordBtn.innerText = "Recording... Click to send";
            cancelBtn.classList.remove('hidden');
            break;
        case 'Processing':
            recordBtn.innerText = "Processing...";
            recordBtn.disabled = true;
            cancelBtn.classList.add('hidden');
            break;
    }
}

recordBtn.onclick = async () => {
    if (state === 'Ready') {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                if (state === 'Processing') {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    handleUpload(audioBlob);
                }
            };

            mediaRecorder.start();
            applyState('Recording');
        } catch (e) {
            console.error("Microphone access denied", e);
        }

    } else if (state === 'Recording') {
        applyState('Processing');
        mediaRecorder.stop();
    }
};

cancelBtn.onclick = () => {
    if (mediaRecorder && state === 'Recording') {
        mediaRecorder.onstop = null;
        mediaRecorder.stop();
        applyState('Ready');
    }
};

async function handleUpload(blob) {
    const formData = new FormData();
    formData.append('file', blob);

    try {
        const response = await fetch('/recording', 
            { 
                method: 'POST', 
                body: formData,
                headers: {
                'EchoJournal-User-ID': USER_ID
                }
            }
        );
        const result = await response.json();
        addEntryToUI(result.user_prompt, result.ai_response);
    } catch (e) {
        alert("Error transcribing voice!" + String(e));
    } finally {
        applyState('Ready');
    }
}

function addEntryToUI(prompt, response) {
    const div = document.createElement('div');
    div.className = 'entry';
    div.innerHTML = `
        <strong>You:</strong>
        <span class="user-text">"${prompt}"</span>
        <hr>
        <strong>AI Reflections:</strong><br>
        ${marked.parse(response)}
    `;
    journalWindow.appendChild(div);
    journalWindow.scrollTo(0, journalWindow.scrollHeight);
    checkEmptyState();
}

document.getElementById('clearBtn').addEventListener('click', async () => {
    if (!confirm("Wipe all context and history?")) return;
    
    const res = await fetch(`/clear`, 
        { 
            method: 'POST',
            headers: {
                'EchoJournal-User-ID': USER_ID
            }
        }
    );
        
    if (res.ok) {
        journalWindow.innerHTML = '';
        checkEmptyState();
    }
});

function getOrCreateUserId() {
    let userId = localStorage.getItem('journal_user_id');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('journal_user_id', userId);
    }
    return userId;
}

const USER_ID = getOrCreateUserId();

async function loadHistory() {
    try {
        const res = await fetch('/history', {
                headers: {
                    'EchoJournal-User-ID': USER_ID
                }
            }
        );
        
        if (res.ok) {
            const history = await res.json();
            const journalWindow = document.getElementById('journal-window');
            journalWindow.innerHTML = ''; 
            
            history.forEach(entry => {
                if (typeof addEntryToUI === 'function') {
                    addEntryToUI(entry.user_prompt, entry.ai_response);
                }
            });
            
            journalWindow.scrollTop = journalWindow.scrollHeight;
        }
    } catch (err) {
        console.error("Failed to load history:", err);
    } finally {
        checkEmptyState();
    }
}

window.addEventListener('DOMContentLoaded', loadHistory);
