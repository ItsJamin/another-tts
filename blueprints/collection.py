import os
import uuid
import csv
from flask import Blueprint, request, jsonify

collection_bp = Blueprint('collection', __name__)

DATA_DIR = 'data'
WAVS_DIR = os.path.join(DATA_DIR, 'wavs')
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.csv')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WAVS_DIR, exist_ok=True)

def get_sentences():
    """Load sentences from data/sentences_de/*.txt"""

    sentence_folder = os.path.join(DATA_DIR, 'sentences_de')
    if os.path.exists(sentence_folder):
        sentences = []
        for filename in os.listdir(sentence_folder):
            if filename.endswith('.txt'):
                filepath = os.path.join(sentence_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_sentences = [line.strip() for line in f if line.strip()]
                    sentences.extend(file_sentences)
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

@collection_bp.route('/get_total_sentences')
def get_total_sentences():
    sentences = get_sentences()
    return jsonify({'total': len(sentences)})

@collection_bp.route('/get_sentence/<int:index>')
def get_sentence(index):
    sentences = get_sentences()
    if 0 <= index < len(sentences):
        return jsonify({'sentence': sentences[index]})
    return jsonify({'error': 'Invalid sentence index'}), 400

@collection_bp.route('/upload_audio/<int:sentence_index>', methods=['POST'])
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

@collection_bp.route('/update_transcript/<int:sentence_index>', methods=['POST'])
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

    return jsonify({'success': True})
