import os
from flask import Flask, jsonify, render_template, send_file
from blueprints.collection import collection_bp

app = Flask(__name__)

# Register blueprint
app.register_blueprint(collection_bp)

DATA_DIR = 'data'
WAVS_DIR = os.path.join(DATA_DIR, 'wavs')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/audio/<filename>')
def get_audio(filename):
    filepath = os.path.join(WAVS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'Audio file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
