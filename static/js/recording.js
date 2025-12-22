let currentSentenceIndex = 0;
let currentAudioBlob = null;
let currentAudioUrl = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let stream = null;
let totalSentences = 99;//{{ total_sentences }};

const recordButton = document.getElementById('recordButton');
const playBtn = document.getElementById('playBtn');
const keepBtn = document.getElementById('keepBtn');
const redoBtn = document.getElementById('redoBtn');
const editBtn = document.getElementById('editBtn');
const saveEditBtn = document.getElementById('saveEditBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');
const transcriptEdit = document.getElementById('transcriptEdit');
const transcriptTextarea = document.getElementById('transcriptTextarea');

async function loadSentence(index) {
    try {
        const response = await fetch(`/get_sentence/${index}`);
        const data = await response.json();
        if (data.sentence) {
            document.getElementById('currentSentence').textContent = data.sentence;
            document.getElementById('currentIndex').textContent = index + 1;
            updateProgressBar();
            resetRecordingState();
        }
    } catch (error) {
        console.error('Error loading sentence:', error);
        document.getElementById('status').textContent = 'Error loading sentence';
    }
}

function updateProgressBar() {
    const percentage = ((currentSentenceIndex + 1) / totalSentences) * 100;
    document.getElementById('progressBar').style.width = percentage + '%';
}

function resetRecordingState() {
    isRecording = false;
    recordButton.classList.remove('recording');
    recordButton.disabled = false;
    playBtn.disabled = true;
    keepBtn.disabled = true;
    document.getElementById('status').textContent = 'Click record or press Space to start';
    if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
        currentAudioUrl = null;
    }
    currentAudioBlob = null;
}

async function startRecording() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        audioChunks = [];
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            currentAudioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            currentAudioUrl = URL.createObjectURL(currentAudioBlob);
            playBtn.disabled = false;
            keepBtn.disabled = false;

            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        recordButton.classList.add('recording');
        document.getElementById('status').textContent = 'Recording... Press Space to stop';
    } catch (error) {
        console.error('Error starting recording:', error);
        document.getElementById('status').textContent = 'Error accessing microphone';
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.classList.remove('recording');
        document.getElementById('status').textContent = 'Recording stopped. Review your audio.';
    }
}

function playRecording() {
    if (currentAudioUrl) {
        const audio = new Audio(currentAudioUrl);
        audio.play();
    }
}

async function keepRecording() {
    if (!currentAudioBlob) return;

    const formData = new FormData();
    formData.append('audio', currentAudioBlob, 'recording.wav');

    try {
        document.getElementById('status').textContent = 'Uploading...';
        const response = await fetch(`/upload_audio/${currentSentenceIndex}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('status').textContent = 'Saved! Moving to next sentence...';
            setTimeout(() => {
                nextSentence();
            }, 1000);
        } else {
            document.getElementById('status').textContent = 'Error saving: ' + data.error;
        }
    } catch (error) {
        console.error('Error uploading:', error);
        document.getElementById('status').textContent = 'Error uploading audio';
    }
}

function nextSentence() {
    currentSentenceIndex++;
    if (currentSentenceIndex >= totalSentences) {
        document.getElementById('status').textContent = 'All sentences completed!';
        recordButton.disabled = true;
        return;
    }
    loadSentence(currentSentenceIndex);
}

function redo() {
    document.getElementById('status').textContent = 'Redo requested. Click record or press Space.';
    resetRecordingState();
}

function editTranscript() {
    transcriptTextarea.value = document.getElementById('currentSentence').textContent;
    transcriptEdit.classList.add('show');
    transcriptTextarea.focus();
}

async function saveTranscript() {
    const newTranscript = transcriptTextarea.value.trim();
    if (!newTranscript) return;

    try {
        const response = await fetch(`/update_transcript/${currentSentenceIndex}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: newTranscript })
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('currentSentence').textContent = newTranscript;
            transcriptEdit.classList.remove('show');
            document.getElementById('status').textContent = 'Transcript updated.';
        } else {
            document.getElementById('status').textContent = 'Error updating transcript.';
        }
    } catch (error) {
        console.error('Error updating transcript:', error);
        document.getElementById('status').textContent = 'Error updating transcript.';
    }
}

function cancelEdit() {
    transcriptEdit.classList.remove('show');
}

// Event listeners
recordButton.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

playBtn.addEventListener('click', playRecording);
keepBtn.addEventListener('click', keepRecording);
redoBtn.addEventListener('click', redo);
editBtn.addEventListener('click', editTranscript);
saveEditBtn.addEventListener('click', saveTranscript);
cancelEditBtn.addEventListener('click', cancelEdit);

// Keyboard shortcuts
document.addEventListener('keydown', event => {
    switch (event.code) {
        case 'Space':
            event.preventDefault();
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
            break;
        case 'Enter':
            if (!keepBtn.disabled) {
                keepRecording();
            }
            break;
        case 'KeyR':
            if (event.ctrlKey || event.metaKey) return; // Allow browser refresh
            redo();
            break;
        case 'KeyE':
            editTranscript();
            break;
    }
});

// Initialize
loadSentence(0);
