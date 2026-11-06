"""Local speech recognition behind one small interface."""

import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass
class Transcript:
    text: str
    language: str | None = None


def read_wav(path: Path) -> np.ndarray:
    """Read 16 kHz mono 16-bit audio as floats in [-1, 1]."""
    with wave.open(str(path)) as f:
        if (f.getframerate(), f.getnchannels(), f.getsampwidth()) != (16_000, 1, 2):
            raise ValueError(f"{path} is not 16 kHz mono 16-bit audio")
        samples = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
    return samples.astype(np.float32) / 32768


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> Transcript: ...


class QwenTranscriber:
    def __init__(self, model: str = "moona3k/mlx-qwen3-asr-0.6b-8bit"):
        from mlx_qwen3_asr import Session

        self.session = Session(model=model)

    def transcribe(self, audio_path: Path) -> Transcript:
        result = self.session.transcribe(str(audio_path))
        return Transcript(result.text.strip(), result.language)


class WhisperTranscriber:
    def __init__(self, model: str = "mlx-community/whisper-large-v3-turbo"):
        self.model = model

    def transcribe(self, audio_path: Path) -> Transcript:
        import mlx_whisper

        result = mlx_whisper.transcribe(read_wav(audio_path), path_or_hf_repo=self.model)
        return Transcript(result["text"].strip(), result.get("language"))


BACKENDS = {"qwen": QwenTranscriber, "whisper": WhisperTranscriber}
