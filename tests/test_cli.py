from pathlib import Path

from archerfish.asr import Transcript
from archerfish.cli import process
from archerfish.rewrite import Rewrite


class FakeTranscriber:
    def transcribe(self, audio_path):
        return Transcript("um fix the test", "English")


class FakeRewriter:
    def __init__(self, result):
        self.result = result
        self.seen = None

    def rewrite(self, transcript):
        self.seen = transcript
        return self.result


def test_passes_transcript_to_rewriter():
    rewriter = FakeRewriter(Rewrite("Fix the test."))
    result = process(Path("a.wav"), FakeTranscriber(), rewriter)
    assert rewriter.seen == "um fix the test"
    assert (result.text, result.fell_back) == ("Fix the test.", False)


def test_reports_fallback():
    result = process(Path("a.wav"), FakeTranscriber(), FakeRewriter(Rewrite("raw", fell_back=True)))
    assert result.fell_back
