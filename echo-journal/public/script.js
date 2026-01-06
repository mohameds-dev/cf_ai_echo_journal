let state = 'Ready';
let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById('recordBtn');
const cancelBtn = document.getElementById('cancelBtn');
const journalWindow = document.getElementById('journal-window');

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

    } else if (state === 'Recording') {
        applyState('Processing');
        mediaRecorder.stop();
    }
};

cancelBtn.onclick = () => {
    if (mediaRecorder && state === 'Recording') {
        mediaRecorder.onstop = null; // Prevent trigger
        mediaRecorder.stop();
        applyState('Ready');
    }
};

async function handleUpload(blob) {
    const formData = new FormData();
    formData.append('file', blob);

    try {
        const response = await fetch('/recording', { method: 'POST', body: formData });
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
}


document.getElementById('clearBtn').addEventListener('click', async () => {
    if (!confirm("Wipe all context and history?")) return;
    const urlParams = new URLSearchParams(window.location.search);
    const key = urlParams.get('key') || '';
    
    const res = await fetch(`/clear?key=${key}`, { method: 'POST' });
    if (res.ok) {
        document.getElementById('journal-window').innerHTML = '';
        alert("Memory wiped.");
    }
});