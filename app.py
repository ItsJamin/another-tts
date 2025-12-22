import os
import uuid
import csv
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

DATA_DIR = 'data'
WAVS_DIR = os.path.join(DATA_DIR, 'wavs')
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.csv')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WAVS_DIR, exist_ok=True)

def get_sentences():
    """Load sentences from data/sentences.txt"""
    sentences_file = os.path.join(DATA_DIR, 'sentences.txt')
    if os.path.exists(sentences_file):
        with open(sentences_file, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]
        return sentences
    return []

def save_metadata(filename, transcript):
    """Save metadata to CSV file"""
    file_exists = os.path.exists(METADATA_FILE)
    with open(METADATA_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'transcript']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='|')
        if not file_exists:
            writer.writeheader()
        writer.writerow({'filename': filename, 'transcript': transcript})

@app.route('/')
def index():
    sentences = get_sentences()
    if not sentences:
        return "No sentences found in data/sentences.txt", 500
    return render_template('index.html', total_sentences=len(sentences))

@app.route('/get_sentence/<int:index>')
def get_sentence(index):
    sentences = get_sentences()
    if 0 <= index < len(sentences):
        return jsonify({'sentence': sentences[index]})
    return jsonify({'error': 'Invalid sentence index'}), 400

@app.route('/upload_audio/<int:sentence_index>', methods=['POST'])
def upload_audio(sentence_index):
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    sentences = get_sentences()

    if not (0 <= sentence_index < len(sentences)):
        return jsonify({'error': 'Invalid sentence index'}), 400

    transcript = sentences[sentence_index]

    # Generate unique filename
    filename = f"recording_{uuid.uuid4().hex}.wav"

    # Read audio data and save directly
    audio_data = audio_file.read()
    filepath = os.path.join(WAVS_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(audio_data)

    # Save metadata
    save_metadata(filename, transcript)

    return jsonify({'success': True, 'filename': filename})

@app.route('/update_transcript/<int:sentence_index>', methods=['POST'])
def update_transcript(sentence_index):
    data = request.get_json()
    new_transcript = data.get('transcript', '').strip()

    if not new_transcript:
        return jsonify({'error': 'Empty transcript'}), 400

    sentences = get_sentences()
    if not (0 <= sentence_index < len(sentences)):
        return jsonify({'error': 'Invalid sentence index'}), 400

    # Update in memory (in real app, you'd update the file)
    sentences[sentence_index] = new_transcript

    # For simplicity, we'll update the metadata.csv if recording was made
    # But this is a simplified version

    return jsonify({'success': True})

@app.route('/audio/<filename>')
def get_audio(filename):
    filepath = os.path.join(WAVS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'Audio file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
