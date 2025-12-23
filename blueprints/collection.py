import os
import uuid
import csv
from flask import Blueprint, request, jsonify
from flask import request, jsonify
from audio_utils import (
    decode_with_ffmpeg,
    enforce_audio_standards,
    write_pcm16_wav
)
import dotenv


collection_bp = Blueprint('collection', __name__)

DATA_DIR = 'data'
WAVS_DIR = os.path.join(DATA_DIR,  'datasets', dotenv.get_key('.env', 'CURRENT_DATASET') or 'your_dataset')
METADATA_FILE = os.path.join(WAVS_DIR, 'metadata.csv')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WAVS_DIR, exist_ok=True)

def get_sentences():
    """Load sentences from data/sentences/de/*.txt"""

    sentence_folder = os.path.join(DATA_DIR, 'sentences', dotenv.get_key('.env', 'CURRENT_LANGUAGE') or 'de')
    if os.path.exists(sentence_folder):
        sentences = []
        for filename in os.listdir(sentence_folder):
            if filename.endswith('.txt'):
                filepath = os.path.join(sentence_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_sentences = [line.strip() for line in f if line.strip()]
                    sentences.extend(file_sentences)
        print("Loaded", len(sentences), "sentences for collection.")
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

    transcript = request.form.get('transcript', '').strip()
    sentences = get_sentences()

    if not transcript:
        if not (0 <= sentence_index < len(sentences)):
            return jsonify({'error': 'Invalid sentence index'}), 400
        transcript = sentences[sentence_index]

    try:
        audio = decode_with_ffmpeg(audio_file)

        # audio = enforce_audio_standards(audio, 44100) # TODO

        filename = f"{sentence_index+1:05d}_{uuid.uuid4().hex[:7]}.wav"

        filepath = os.path.join(WAVS_DIR, filename)

        write_pcm16_wav(filepath, audio, 44100)

        save_metadata(filename, transcript)

        return jsonify({
            'success': True,
            'filename': filename,
            # 'lufs': round(lufs, 2),
            # 'peak_dbfs': round(peak_dbfs, 2)
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500


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


@collection_bp.route('/update_transcript', methods=['POST'])
def update_transcript_for_file():
    """
    Update the transcript stored in metadata.csv for a specific filename.
    Expects JSON: { "filename": "<recording filename>", "transcript": "<new transcript>" }
    If the filename is not present in metadata, a new entry will be appended.
    """
    data = request.get_json() or {}
    filename = data.get('filename', '').strip()
    new_transcript = data.get('transcript', '').strip()

    if not filename:
        return jsonify({'error': 'Missing filename'}), 400
    if not new_transcript:
        return jsonify({'error': 'Empty transcript'}), 400

    rows = []
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')
            for r in reader:
                rows.append(r)

    found = False
    for r in rows:
        if r.get('filename') == filename:
            r['transcript'] = new_transcript
            found = True
            break

    if not found:
        rows.append({'filename': filename, 'transcript': new_transcript})

    # Write back whole CSV
    with open(METADATA_FILE, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['filename', 'transcript']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return jsonify({'success': True})
