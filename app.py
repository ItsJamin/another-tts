import os
import sys
import shutil
import dotenv
from flask import Flask, jsonify, render_template, send_file

from blueprints.collection import collection_bp
from blueprints.export import export_bp


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

ENV_DIR = os.path.join(BASE_DIR, "env")
ENV_PATH = os.path.join(ENV_DIR, ".env")
ENV_EXAMPLE_PATH = os.path.join(BASE_DIR, ".env.example")

DATA_DIR = os.path.join(BASE_DIR, "data")
SENTENCES_DIR = os.path.join(DATA_DIR, "sentences")


def ensure_env():
    os.makedirs(ENV_DIR, exist_ok=True)

    if not os.path.exists(ENV_PATH):
        if os.path.exists(ENV_EXAMPLE_PATH):
            shutil.copy(ENV_EXAMPLE_PATH, ENV_PATH)
        else:
            open(ENV_PATH, "a").close()

    dotenv.load_dotenv(ENV_PATH)


def ensure_sentences_data():
    if not getattr(sys, "frozen", False):
        return

    bundled_base = sys._MEIPASS
    bundled_sentences = os.path.join(bundled_base, "data", "sentences")

    if not os.path.exists(bundled_sentences):
        return

    if os.path.exists(SENTENCES_DIR):
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    shutil.copytree(bundled_sentences, SENTENCES_DIR)


def create_app():
    ensure_env()
    ensure_sentences_data()

    app = Flask(__name__)

    app.register_blueprint(collection_bp)
    app.register_blueprint(export_bp)

    dataset = os.getenv("CURRENT_DATASET") or "your_dataset"
    wavs_dir = os.path.join(DATA_DIR, "datasets", dataset)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/audio/<filename>")
    def get_audio(filename):
        filepath = os.path.join(wavs_dir, filename)

        if os.path.exists(filepath):
            return send_file(filepath)

        return jsonify({"error": "Audio file not found"}), 404

    return app


def main():
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5067,
        debug=False
    )


if __name__ == "__main__":
    main()
