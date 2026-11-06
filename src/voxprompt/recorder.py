"""Microphone capture."""

import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000


class Microphone:
    """Keeps one input stream open, because stopping a stream can deadlock CoreAudio."""

    def __init__(self):
        self.chunks = None
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=self._on_audio
        )
        self.stream.start()

    def _on_audio(self, data, *_):
        if self.chunks is not None:
            self.chunks.append(data.copy())

    def begin(self) -> None:
        self.chunks = []

    def end(self) -> np.ndarray:
        chunks, self.chunks = self.chunks, None
        return np.concatenate(chunks) if chunks else np.zeros((0, 1), dtype=np.int16)


def is_silent(samples: np.ndarray) -> bool:
    """True for digital silence. A working microphone always picks up some noise."""
    return not np.any(samples)


def write_wav(path: Path, samples: np.ndarray) -> None:
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(samples.tobytes())
