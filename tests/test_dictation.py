import numpy as np
import pytest

from archerfish.asr import Transcript
from archerfish.dictation import Dictation, State
from archerfish.recorder import SAMPLE_RATE
from archerfish.rewrite import Rewrite

SPEECH = np.ones((SAMPLE_RATE, 1), dtype=np.int16)


class FakeMic:
    def __init__(self, samples=SPEECH):
        self.samples = samples
        self.begun = 0

    def begin(self):
        self.begun += 1

    def end(self):
        return self.samples


class FakeTranscriber:
    def __init__(self, text="um fix it"):
        self.text = text

    def transcribe(self, path):
        assert path.exists()
        return Transcript(self.text)


class FakeRewriter:
    def __init__(self, fell_back=False):
        self.fell_back = fell_back

    def rewrite(self, transcript):
        return Rewrite("Fix it.", self.fell_back)


def make(mic=None, text="um fix it", fell_back=False, pasted=True):
    pastes = []

    def paste(value):
        pastes.append(value)
        return pasted

    dictation = Dictation(mic or FakeMic(), None, FakeRewriter(fell_back), paste)
    dictation.transcriber = FakeTranscriber(text)
    dictation.state = State.READY
    return dictation, pastes


def speak(dictation):
    dictation.press()
    dictation.release()
    if not dictation.jobs.empty():
        dictation.handle(dictation.jobs.get())


def test_pastes_the_rewritten_text():
    dictation, pastes = make()
    speak(dictation)
    assert pastes == ["Fix it."]
    assert (dictation.state, dictation.message) == (State.READY, "")


def test_short_press_is_ignored():
    dictation, pastes = make(FakeMic(SPEECH[:100]))
    speak(dictation)
    assert pastes == []
    assert dictation.state is State.READY


def test_press_is_ignored_while_working():
    mic = FakeMic()
    dictation, _ = make(mic)
    dictation.press()
    dictation.release()
    dictation.press()
    assert mic.begun == 1
    assert dictation.state is State.WORKING


def test_press_is_ignored_while_loading():
    mic = FakeMic()
    dictation, _ = make(mic)
    dictation.state = State.LOADING
    dictation.press()
    assert mic.begun == 0


@pytest.mark.parametrize("kwargs, expected", [
    ({"mic": FakeMic(np.zeros((SAMPLE_RATE, 1), dtype=np.int16))}, "No sound"),
    ({"text": ""}, "catch that"),
    ({"pasted": False}, "clipboard"),
    ({"fell_back": True}, "Cleanup failed"),
])
def test_problems_are_reported(kwargs, expected):
    dictation, _ = make(**kwargs)
    speak(dictation)
    assert expected in dictation.message
    assert dictation.state is State.READY


def test_worker_survives_an_error():
    dictation, pastes = make()
    dictation.transcriber = None
    speak(dictation)
    assert "went wrong" in dictation.message
    assert dictation.state is State.READY
    assert pastes == []
