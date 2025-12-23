# Another TTS

Easy Workflow for creating Training Data for TTS.

<img width="1853" height="845" alt="interface of record session" src="https://github.com/user-attachments/assets/857ef023-99d0-4429-93bc-53d9829d1dfe" />


# Installation

### Docker-Way

```
git clone https://github.com/ItsJamin/another-tts
cd another-tts
cp .env.example .env
docker compose up
```

### Python-Way

- Create `.venv` (Python 3.13.7)
    `python -m venv .venv`

- Activate Virtual Environment
    Linux: `source .venv/bin/activate`
    Windows: `.venv\Scripts\activate`

- Install Libraries:
    `pip install -r requirements.txt`

- Install `ffmpeg` if not in system (needs to be available on cmd with `ffmpeg`)

- Create in the root directory a `.env`-File with the following content:

```.env
CURRENT_DATASET = "<your_dataset_name>"
CURRENT_LANGUAGE = "de" # currently only german sentences
```

Change the name of your dataset to what your dataset should be called.

- Start Server with `python app.py` and visit `localhost:5000`

# Data

- `data/sentences/CURRENT_LANGUAGE/` - Textfiles of what to say
- `data/datasets/CURRENT_DATASET/` - Place where recordings are saved.
- `data/datasets/CURRENT_DATASET/metadata.csv` - Which audiofiles contain what text. (see `example` Dataset)

# TODO

- [x] GUI for easily recording Data
- [ ] GUI for Overview over recorded Data
- [ ] Filter out already recorded lines

- [ ] Training of Data? (maybe in another project)
- [ ] Metadata for voice (mood, whisper, etc.)?
- [ ] Docker Implementation

***

# Standards

### What criteria should lines follow?

* Transcript text must match the spoken audio verbatim
* No paraphrasing, omissions, or additions
* All text must be fully normalized (numbers, dates, abbreviations, special symbols written out)
* DO use points, question marks, commatas and apostrophs.
* No inconsistent or ambiguous punctuation
* One sentence per line
* Neutral, non-acted language (does not mean boring)
* Lines should vary in length (short, medium, long) to ensure phonetic coverage
* Questions, statements, numbers, dates, and abbreviations must be represented
* The same text normalization rules must be applied consistently across the entire dataset

Examples:
- I have 42 apples. -> I have forty two apples.
- The contract was signed in 2025. -> The contract was signed in twenty twenty five.
- Dr. Smith will arrive at 9 a.m. -> Doctor Smith will arrive at nine a m.
- The battery is at 80%. -> The battery is at eighty percent.
- "Wait, how did you 2 meet again?" -> Wait, how did you two meet again?

---

### What criteria should recordings follow?

* WAV format, PCM (uncompressed), mono
* Consistent sample rate across all files
* Recommended: 44.1 kHz, 16-bit
* One sentence per file
* File duration ideally between 1.5 and 8 seconds
* No leading or trailing silence greater than ~200 ms
* No clipping, distortion, or background noise
* Stable loudness across all recordings
* Target: −20 to −16 LUFS, peak below −1 dBFS
* Recorded in the same environment with the same microphone and setup
* Fixed microphone distance and speaking posture
* Consistent speaking style, pace, and energy level
* No whispering, shouting, or expressive acting
* Speaker must be healthy and vocally consistent across sessions
* File names must be deterministic, sortable, and space-free (e.g. `speaker_0001.wav`)
* Stereo files, variable sample rates, and inconsistent bit depth are not allowed
