from flask import Flask, render_template, send_file
from blueprints.collection import collection_bp
import os

app = Flask(__name__)

# Register blueprint
app.register_blueprint(collection_bp)

DATA_DIR = 'data'
WAVS_DIR = os.path.join(DATA_DIR, 'wavs')

def get_sentences():
    """Load sentences from data/sentences.txt"""
    import os
    sentences_file = os.path.join(DATA_DIR, 'sentences.txt')
    if os.path.exists(sentences_file):
        with open(sentences_file, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]
        return sentences
    return []

@app.route('/')
def index():
    sentences = get_sentences()
    if not sentences:
        return "No sentences found in data/sentences.txt", 500
    return render_template('index.html', total_sentences=len(sentences))

@app.route('/audio/<filename>')
def get_audio(filename):
    filepath = os.path.join(WAVS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'Audio file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
