import subprocess
import numpy as np
import pyloudnorm as pyln
import wave
import io

TARGET_SAMPLE_RATE = 44100
TARGET_CHANNELS = 1

TARGET_LUFS_MIN = -20.0
TARGET_LUFS_MAX = -16.0
TARGET_PEAK_DBFS = -1.0

MAX_SILENCE_SEC = 0.2


def decode_with_ffmpeg(file_storage):
    # Decode arbitrary browser audio (e.g. WebM/Opus) to float32 PCM mono
    file_storage.stream.seek(0)
    input_bytes = file_storage.read()

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-f", "f32le",
        "-ac", str(TARGET_CHANNELS),
        "-ar", str(TARGET_SAMPLE_RATE),
        "pipe:1",
    ]

    proc = subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if proc.returncode != 0 or not proc.stdout:
        raise ValueError("FFmpeg decoding failed")

    audio = np.frombuffer(proc.stdout, dtype=np.float32)
    return audio


def trim_silence(audio, sr):
    # Simple energy-based trimming
    abs_audio = np.abs(audio)
    threshold = 1e-4

    non_silent = np.where(abs_audio > threshold)[0]
    if non_silent.size == 0:
        return audio

    start = max(0, non_silent[0] - int(MAX_SILENCE_SEC * sr))
    end = min(len(audio), non_silent[-1] + int(MAX_SILENCE_SEC * sr))

    return audio[start:end]


def analyze_loudness(audio, sr):
    meter = pyln.Meter(sr)
    lufs = meter.integrated_loudness(audio)

    peak = np.max(np.abs(audio))
    peak_dbfs = 20.0 * np.log10(max(peak, 1e-9))

    return lufs, peak_dbfs


def normalize_loudness(audio, sr, target_lufs):
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio)

    return pyln.normalize.loudness(
        audio,
        current_lufs,
        target_lufs
    )


def enforce_audio_standards(audio, sr):
    audio = trim_silence(audio, sr)

    lufs, peak_dbfs = analyze_loudness(audio, sr)

    if peak_dbfs >= 0.0:
        raise ValueError("Clipping detected (peak >= 0 dBFS)")

    if lufs < TARGET_LUFS_MIN or lufs > TARGET_LUFS_MAX:
        target = (TARGET_LUFS_MIN + TARGET_LUFS_MAX) / 2.0
        audio = normalize_loudness(audio, sr, target)
        lufs, peak_dbfs = analyze_loudness(audio, sr)

    if peak_dbfs > TARGET_PEAK_DBFS:
        raise ValueError("Peak exceeds allowed maximum after normalization")

    return audio, lufs, peak_dbfs


def write_pcm16_wav(path, audio, sr):
    # Convert float32 [-1,1] to int16 PCM
    audio_int16 = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
