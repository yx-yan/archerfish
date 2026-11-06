"""Record each line of scripts.tsv, read aloud, into evals/samples/."""

import argparse
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np

from voxprompt.recorder import Microphone, is_silent, write_wav

EVALS = Path(__file__).parent
NO_SOUND = """No sound from the microphone: every sample is exactly zero.
macOS does this when the app running this script has no microphone access.
Run this from Terminal.app and allow the prompt, or turn the app on under
System Settings > Privacy & Security > Microphone and restart it."""


def read_samples(path: Path) -> np.ndarray:
    with wave.open(str(path)) as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)


def run(redo: bool) -> None:
    samples = EVALS / "samples"
    samples.mkdir(exist_ok=True)

    mic = Microphone()
    mic.begin()
    time.sleep(1)
    if is_silent(mic.end()):
        print(NO_SOUND)
        return

    for line in (EVALS / "scripts.tsv").read_text().splitlines():
        sample_id, text = line.split("\t")
        path = samples / f"{sample_id}.wav"
        if path.exists() and not redo and not is_silent(read_samples(path)):
            continue
        print(f"\n[{sample_id}] {text}")
        input("  Press Enter, then read it at your normal pace. ")
        mic.begin()
        input("  Recording. Press Enter when you finish. ")
        recording = mic.end()
        if is_silent(recording):
            print(NO_SOUND)
            return
        write_wav(path, recording)
    print("\nAll samples recorded.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--redo", action="store_true", help="record over existing samples")
    args = parser.parse_args()
    run(args.redo)
    sys.stdout.flush()
    os._exit(0)  # Skip closing the stream, which is where CoreAudio can deadlock.


if __name__ == "__main__":
    main()
