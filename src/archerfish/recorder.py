"""Microphone capture."""

import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
QUIET_DB, LOUD_DB = -55, -25  # Room noise to loud speech, from the benchmark recordings.


class Microphone:
    """Keeps one input stream open, because stopping a stream can deadlock CoreAudio."""

    def __init__(self):
        self.chunks = None
        self.level = 0.0
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=self._on_audio
        )
        self.stream.start()

    def _on_audio(self, data, *_):
        if self.chunks is not None:
            self.chunks.append(data.copy())
            self.level = loudness(data)

    def begin(self) -> None:
        self.level = 0.0
        self.chunks = []

    def end(self) -> np.ndarray:
        chunks, self.chunks = self.chunks, None
        return np.concatenate(chunks) if chunks else np.zeros((0, 1), dtype=np.int16)


def loudness(samples: np.ndarray) -> float:
    """Map a block of audio to 0-1, on a decibel scale because that is how loudness feels."""
    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2)) / 32768
    if rms == 0:
        return 0.0
    return float(np.clip((20 * np.log10(rms) - QUIET_DB) / (LOUD_DB - QUIET_DB), 0, 1))


def is_silent(samples: np.ndarray) -> bool:
    """True for digital silence. A working microphone always picks up some noise."""
    return not np.any(samples)


def write_wav(path: Path, samples: np.ndarray) -> None:
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(samples.tobytes())
