import os
import csv
import wave
from flask import Blueprint, render_template
import dotenv

export_bp = Blueprint('export', __name__, template_folder='templates')

DATA_DIR = 'data'
WAVS_DIR = os.path.join(
    DATA_DIR,
    'datasets',
    dotenv.get_key('env/.env', 'CURRENT_DATASET') or 'your_dataset'
)

METADATA_FILE = os.path.join(WAVS_DIR, 'metadata.csv')


def get_audio_statistics_from_metadata():
    """
    Read metadata.csv and calculate statistics based on referenced WAV files.
    """

    total_entries = 0
    valid_files = 0
    missing_files = 0
    error_files = 0
    total_duration = 0.0

    if not os.path.exists(METADATA_FILE):
        return {
            'total_entries': 0,
            'valid_files': 0,
            'missing_files': 0,
            'error_files': 0,
            'total_duration': 0.0
        }

    with open(METADATA_FILE, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='|')

        for row in reader:
            total_entries += 1

            filename = row.get('filename', '').strip()
            if not filename:
                error_files += 1
                continue

            filepath = os.path.join(WAVS_DIR, filename)

            if not os.path.exists(filepath):
                missing_files += 1
                continue

            try:
                with wave.open(filepath, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)

                    total_duration += duration
                    valid_files += 1

            except wave.Error:
                error_files += 1
                continue

    return {
        'total_entries': total_entries,
        'valid_files': valid_files,
        'missing_files': missing_files,
        'error_files': error_files,
        'total_duration': total_duration
    }


@export_bp.route('/export')
def export_overview():
    stats = get_audio_statistics_from_metadata()

    return render_template(
        'export.html',
        stats=stats
    )
