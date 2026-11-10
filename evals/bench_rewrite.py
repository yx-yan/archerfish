"""Time the rewrite step and print its output for review. Calls the DeepSeek API."""

import argparse
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from archerfish.rewrite import Rewriter

EVALS = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    load_dotenv(EVALS.parent / ".env")
    rewriter = Rewriter()
    cases = [
        line.split("\t") for line in (EVALS / "rewrite_cases.tsv").read_text().splitlines()
    ]

    latencies = []
    for case_id, transcript in cases:
        for _ in range(args.repeats):
            start = time.perf_counter()
            result = rewriter.rewrite(transcript)
            latencies.append(time.perf_counter() - start)
        fallback = " [FELL BACK]" if result.fell_back else ""
        print(f"\n[{case_id}] {latencies[-1]:.2f}s{fallback}\n  in:  {transcript}\n  out: {result.text}")

    print(f"\nmedian {statistics.median(latencies):.2f}s, max {max(latencies):.2f}s, "
          f"{len(latencies)} calls")


if __name__ == "__main__":
    main()
