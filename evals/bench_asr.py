"""Measure one ASR backend's accuracy, latency and memory on the recorded samples.

Run one backend per process so peak memory is not shared between models.
"""

import argparse
import json
import statistics
import time
import wave
from pathlib import Path

import mlx.core as mx

from metrics import error_rate
from voxprompt.asr import BACKENDS

EVALS = Path(__file__).parent


def duration(path: Path) -> float:
    with wave.open(str(path)) as f:
        return f.getnframes() / f.getframerate()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=BACKENDS, required=True)
    parser.add_argument("--samples", type=Path, default=EVALS / "samples")
    args = parser.parse_args()

    references = dict(
        line.split("\t") for line in (EVALS / "scripts.tsv").read_text().splitlines()
    )
    paths = sorted(p for p in args.samples.glob("*.wav") if p.stem in references)
    if not paths:
        raise SystemExit(f"No samples in {args.samples}. Run record_samples.py first.")

    transcriber = BACKENDS[args.backend]()
    transcriber.transcribe(paths[0])  # Warm up: the app keeps its model loaded.

    rows = []
    for path in paths:
        start = time.perf_counter()
        transcript = transcriber.transcribe(path)
        seconds = time.perf_counter() - start
        language = path.stem.split("-")[0]
        rows.append({
            "id": path.stem,
            "audio_seconds": round(duration(path), 2),
            "latency_seconds": round(seconds, 3),
            "error_rate": round(error_rate(references[path.stem], transcript.text, language), 4),
            "detected_language": transcript.language,
            "text": transcript.text,
        })
        print(f"{path.stem}  {rows[-1]['audio_seconds']:5.1f}s audio  "
              f"{seconds:5.2f}s  err {rows[-1]['error_rate']:.1%}  {transcript.text}")

    print(f"\n{args.backend}: peak GPU memory {mx.get_peak_memory() / 2**30:.2f} GB")
    for language in ("zh", "en"):
        group = [r for r in rows if r["id"].startswith(language)]
        if group:
            print(f"{language}: mean error {statistics.mean(r['error_rate'] for r in group):.1%}, "
                  f"median latency {statistics.median(r['latency_seconds'] for r in group):.2f}s")

    results = EVALS / "results"
    results.mkdir(exist_ok=True)
    (results / f"{args.backend}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
