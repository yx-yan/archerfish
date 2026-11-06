"""The hold-to-talk flow: record, transcribe, rewrite, paste."""

import queue
import sys
import tempfile
from collections.abc import Callable
from enum import Enum
from pathlib import Path

import numpy as np

from quoth.asr import Transcriber
from quoth.recorder import SAMPLE_RATE, is_silent, write_wav
from quoth.rewrite import Rewriter

MIN_SECONDS = 0.3  # Shorter presses are accidents, such as typing an Option shortcut.


class State(Enum):
    LOADING = "Loading model"
    READY = "Ready"
    RECORDING = "Recording"
    WORKING = "Working"


class Dictation:
    def __init__(
        self,
        mic,
        load_transcriber: Callable[[], Transcriber],
        rewriter: Rewriter,
        paste: Callable[[str], bool],
    ):
        self.mic = mic
        self.load_transcriber = load_transcriber
        self.rewriter = rewriter
        self.paste = paste
        self.state = State.LOADING
        self.message = ""
        self.jobs = queue.Queue()
        self.transcriber = None

    def press(self) -> None:
        if self.state is State.READY:
            self.message = ""
            self.mic.begin()
            self.state = State.RECORDING

    def release(self) -> None:
        if self.state is not State.RECORDING:
            return
        samples = self.mic.end()
        if len(samples) < MIN_SECONDS * SAMPLE_RATE:
            self.state = State.READY
        else:
            self.state = State.WORKING
            self.jobs.put(samples)

    def run(self) -> None:
        """Worker thread. MLX needs loading and inference on the same thread."""
        self.transcriber = self.load_transcriber()
        self.transcribe(np.zeros((SAMPLE_RATE, 1), dtype=np.int16))  # Warm up.
        self.state = State.READY
        while True:
            self.handle(self.jobs.get())

    def handle(self, samples: np.ndarray) -> None:
        try:
            self.message = self.process(samples)
        except Exception as error:
            print(f"Dictation failed: {error!r}", file=sys.stderr)
            self.message = "Something went wrong; see the log"
        self.state = State.READY

    def process(self, samples: np.ndarray) -> str:
        if is_silent(samples):
            return "No sound: check microphone access"
        transcript = self.transcribe(samples)
        if not transcript:
            return "Heard nothing"
        rewrite = self.rewriter.rewrite(transcript)
        if not self.paste(rewrite.text):
            return "Text is on the clipboard: Accessibility access is off"
        return "Rewrite failed, pasted raw text" if rewrite.fell_back else ""

    def transcribe(self, samples: np.ndarray) -> str:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speech.wav"
            write_wav(path, samples)
            return self.transcriber.transcribe(path).text
