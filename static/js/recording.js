let currentSentenceIndex = 0;
let currentAudioBlob = null;
let currentAudioUrl = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let stream = null;
let totalSentences = -1;
let savedFilenames = {};
let audioPlayer = null;

const recordButton = document.getElementById('recordButton');
const waveformDiv = document.getElementById('waveform');
const waveformBar = document.getElementById('waveformBar');
const playBtn = document.getElementById('playBtn');
const keepBtn = document.getElementById('keepBtn');
const redoBtn = document.getElementById('redoBtn');
const editBtn = document.getElementById('editBtn');
const saveEditBtn = document.getElementById('saveEditBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');
const transcriptEdit = document.getElementById('transcriptEdit');
const transcriptTextarea = document.getElementById('transcriptTextarea');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const sentenceInput = document.getElementById('sentenceNumberInput');

async function fetchTotalSentences() {
    try {
        const response = await fetch('/get_total_sentences');
        const data = await response.json();
        totalSentences = data.total;
        sentenceInput.max = totalSentences;
    } catch (error) {
        console.error('Error fetching total:', error);
        totalSentences = -1; // fallback
    }
}

async function loadSentence(index) {
    try {
        const response = await fetch(`/get_sentence/${index}`);
        const data = await response.json();
        if (data.sentence) {
            document.getElementById('currentSentence').textContent = data.sentence;
            sentenceInput.value = index + 1;
            resetRecordingState();
        }
    } catch (error) {
        console.error('Error loading sentence:', error);
        document.getElementById('status').textContent = 'Error loading sentence';
    }
}

function navigateToSentence(index) {
    if (index >= 0 && index < totalSentences) {
        currentSentenceIndex = index;
        loadSentence(currentSentenceIndex);
    } else {
        sentenceInput.value = currentSentenceIndex + 1;
    }
}

function resetRecordingState() {
    isRecording = false;
    recordButton.classList.remove('recording');
    recordButton.style.display = 'block';
    waveformDiv.style.display = 'none';
    playBtn.disabled = true;
    keepBtn.disabled = true;
    document.getElementById('status').textContent = 'Click record or press Space to start';
    if (audioPlayer) {
        try { audioPlayer.pause(); } catch (e) {}
        audioPlayer = null;
    }
    if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
        currentAudioUrl = null;
    }
    currentAudioBlob = null;
    if (waveformBar) waveformBar.style.width = '0%';
    const currentTimeEl = document.getElementById('currentTime');
    const durationTimeEl = document.getElementById('durationTime');
    if (currentTimeEl) currentTimeEl.textContent = '0:00';
    if (durationTimeEl) durationTimeEl.textContent = '0:00';
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
            showWaveform();
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

function showWaveform() {
    recordButton.style.display = 'none';
    waveformDiv.style.display = 'block';
    waveformBar.style.width = '0%';
    const currentTimeEl = document.getElementById('currentTime');
    const durationTimeEl = document.getElementById('durationTime');
    if (currentTimeEl) currentTimeEl.textContent = '0:00';
    if (durationTimeEl) durationTimeEl.textContent = '0:00';
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.classList.remove('recording');
        document.getElementById('status').textContent = 'Recording stopped. Review your audio.';
        playBtn.disabled = false;
        keepBtn.disabled = false;
    }
}

function formatTime(seconds) {
    if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function playRecording() {
    if (!currentAudioUrl) return;

    // If there's an existing player that's paused/playing, toggle play/pause
    if (audioPlayer && !audioPlayer.ended) {
        if (audioPlayer.paused) {
            audioPlayer.play().then(() => {
                document.getElementById('status').textContent = 'Playing...';
            }).catch(err => {
                console.error('Playback error:', err);
            });
        } else {
            audioPlayer.pause();
            document.getElementById('status').textContent = 'Paused';
        }
        return;
    }

    audioPlayer = new Audio(currentAudioUrl);
    audioPlayer.preload = 'metadata';

    // Use a fixed nominal duration (1 minute) for progress bar mapping

    const currentTimeEl = document.getElementById('currentTime');
    const durationTimeEl = document.getElementById('durationTime');

    audioPlayer.addEventListener('loadedmetadata', () => {
        if (durationTimeEl) durationTimeEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener('timeupdate', () => {
        const elapsed = Math.max(0, audioPlayer.currentTime || 0);
        const pct = Math.min((elapsed / audioPlayer.duration) * 100, 100);
        waveformBar.style.width = pct + '%';
        console.log(pct, elapsed);
        if (currentTimeEl) currentTimeEl.textContent = formatTime(elapsed);
    });

    audioPlayer.addEventListener('ended', () => {
        waveformBar.style.width = '100%';
        if (currentTimeEl) currentTimeEl.textContent = formatTime(audioPlayer.duration);
        document.getElementById('status').textContent = 'Playback finished.';
        audioPlayer = null;
    });

    audioPlayer.play().then(() => {
        document.getElementById('status').textContent = 'Playing...';
    }).catch(err => {
        console.error('Playback error:', err);
        document.getElementById('status').textContent = 'Playback error';
    });
}

async function keepRecording() {
    if (!currentAudioBlob) return;

    const formData = new FormData();
    formData.append('audio', currentAudioBlob, 'recording.wav');

    // send current transcript from frontend if available
    const currentTranscript = document.getElementById('currentSentence').textContent || '';
    if (currentTranscript.trim()) {
        formData.append('transcript', currentTranscript.trim());
    }

    try {
        document.getElementById('status').textContent = 'Uploading...';
        const response = await fetch(`/upload_audio/${currentSentenceIndex}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            // store returned filename so later edits can update metadata
            if (data.filename) {
                savedFilenames[currentSentenceIndex] = data.filename;
            }
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
    showRecordingButton();
    document.getElementById('status').textContent = 'Redo requested. Click record or press Space.';
    resetRecordingState();
}

function showRecordingButton() {
    waveformDiv.style.display = 'none';
    recordButton.style.display = 'block';
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
        const filename = savedFilenames[currentSentenceIndex];
        let response, data;

        if (filename) {
            // Update metadata for the specific file
            response = await fetch(`/update_transcript`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: filename, transcript: newTranscript })
            });
            data = await response.json();
        } else {
            // Fallback to sentence-index based update
            response = await fetch(`/update_transcript/${currentSentenceIndex}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript: newTranscript })
            });
            data = await response.json();
        }

        if (data && data.success) {
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

waveformDiv.addEventListener('click', playRecording);
playBtn.addEventListener('click', playRecording);
keepBtn.addEventListener('click', keepRecording);
redoBtn.addEventListener('click', () => {
    showRecordingButton();
    resetRecordingState();
});
editBtn.addEventListener('click', editTranscript);
saveEditBtn.addEventListener('click', saveTranscript);
cancelEditBtn.addEventListener('click', cancelEdit);

// Navigation event listeners
prevBtn.addEventListener('click', () => {
    if (currentSentenceIndex > 0) {
        navigateToSentence(currentSentenceIndex - 1);
    }
});

nextBtn.addEventListener('click', () => {
    if (currentSentenceIndex < totalSentences - 1) {
        navigateToSentence(currentSentenceIndex + 1);
    }
});

sentenceInput.addEventListener('change', () => {
    const targetIndex = parseInt(sentenceInput.value) - 1;
    navigateToSentence(targetIndex);
});

// Keyboard shortcuts
document.addEventListener('keydown', event => {
    if (event.target.tagName === 'TEXTAREA') return; // Ignore textarea

    switch (event.code) {
        case 'Space':
            event.preventDefault();
            if (isRecording) {
                stopRecording();
            } else if (currentAudioBlob) {
                playRecording();
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
            if (event.ctrlKey || event.metaKey) return;
            redo();
            break;
        case 'KeyE':
            editTranscript();
            break;
        case 'ArrowLeft':
            event.preventDefault();
            if (currentSentenceIndex > 0) {
                navigateToSentence(currentSentenceIndex - 1);
            }
            break;
        case 'ArrowRight':
            event.preventDefault();
            if (currentSentenceIndex < totalSentences - 1) {
                navigateToSentence(currentSentenceIndex + 1);
            }
            break;

        default:
            break;
        }
});

document.addEventListener('DOMContentLoaded', async () => {
    await fetchTotalSentences();
    loadSentence(currentSentenceIndex);
});
