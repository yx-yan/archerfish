"""Error rates for comparing a transcript with its reference text."""

import unicodedata


def normalize(text: str) -> str:
    kept = (c for c in text.lower() if unicodedata.category(c)[0] not in "PS")
    return " ".join("".join(kept).split())


def edit_distance(a: list[str], b: list[str]) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        previous, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            previous, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, previous + (x != y))
    return row[-1]


def error_rate(reference: str, hypothesis: str, language: str) -> float:
    """Character error rate for Chinese, word error rate for English."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    if language == "zh":
        ref_units, hyp_units = list(ref.replace(" ", "")), list(hyp.replace(" ", ""))
    else:
        ref_units, hyp_units = ref.split(), hyp.split()
    return edit_distance(ref_units, hyp_units) / max(len(ref_units), 1)
