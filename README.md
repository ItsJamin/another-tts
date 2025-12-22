# Another TTS

Easy Workflow for creating Training Data for TTS.

### Installation

- Create `.venv` (Python 3.13.7)
    `python -m venv .venv`

- Activate Virtual Environment
    Linux: `source .venv/bin/activate`
    Windows: `.venv\Scripts\activate`

- Install Libraries:
    `pip install -r requirements.txt`

- Start Server with `python app.py`

### Data

- `data/sentences_*/` - Textfiles of what to say
- `data/wavs/` - Place where recordings are saved.
- `data/metadata.csv` - Which audiofiles contain what text.


### TODO

- [ ] GUI for easily recording Data
- [ ] GUI for Overview over recorded Data

- [ ] Training of Data? (maybe in another project)
- [ ] Metadata for voice (mood, whisper, etc.)?