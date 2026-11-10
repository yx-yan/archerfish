from archerfish.onboarding import Check, has_key, incomplete


def check(done):
    return Check("Name", "Detail", lambda: done)


def test_incomplete_while_anything_is_missing():
    assert incomplete((check(True), check(False)))


def test_complete_when_everything_is_done():
    assert not incomplete((check(True), check(True)))


def test_empty_key_counts_as_missing(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    assert not has_key()
