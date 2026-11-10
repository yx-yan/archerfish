"""Turn an audio file into a clean prompt from the command line."""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from archerfish.asr import QwenTranscriber, Transcriber
from archerfish.rewrite import Rewriter


@dataclass
class Result:
    text: str
    fell_back: bool
    asr_seconds: float
    rewrite_seconds: float


def process(audio_path: Path, transcriber: Transcriber, rewriter: Rewriter) -> Result:
    start = time.perf_counter()
    transcript = transcriber.transcribe(audio_path)
    transcribed = time.perf_counter()
    rewrite = rewriter.rewrite(transcript.text)
    done = time.perf_counter()
    return Result(rewrite.text, rewrite.fell_back, transcribed - start, done - transcribed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, nargs="+", help="16 kHz mono WAV files")
    args = parser.parse_args()

    load_dotenv()
    transcriber = QwenTranscriber()
    transcriber.transcribe(args.audio[0])  # Warm up: the app keeps its model loaded.
    rewriter = Rewriter()
    for path in args.audio:
        result = process(path, transcriber, rewriter)
        note = ", rewrite failed, using raw transcript" if result.fell_back else ""
        print(f"{path.name}: asr {result.asr_seconds:.2f}s, rewrite {result.rewrite_seconds:.2f}s, "
              f"total {result.asr_seconds + result.rewrite_seconds:.2f}s{note}", file=sys.stderr)
        print(result.text)


if __name__ == "__main__":
    main()
