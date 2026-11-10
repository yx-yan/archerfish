import pytest
from AppKit import NSPasteboard, NSPasteboardTypeString

from archerfish import paste as paste_module
from archerfish.paste import paste


@pytest.fixture
def pasteboard():
    # A private pasteboard, so tests never touch the real clipboard.
    board = NSPasteboard.pasteboardWithUniqueName()
    board.clearContents()
    board.setString_forType_("old", NSPasteboardTypeString)
    yield board
    board.releaseGlobally()


@pytest.fixture(autouse=True)
def no_delay(monkeypatch):
    monkeypatch.setattr(paste_module, "RESTORE_DELAY", 0)


def read(board):
    return board.stringForType_(NSPasteboardTypeString)


def test_text_is_on_the_clipboard_during_paste_then_restored(pasteboard):
    during = []
    assert paste("new", pasteboard, lambda: during.append(read(pasteboard)), lambda: True)
    assert during == ["new"]
    assert read(pasteboard) == "old"


def test_empty_clipboard_stays_empty(pasteboard):
    pasteboard.clearContents()
    paste("new", pasteboard, lambda: None, lambda: True)
    assert read(pasteboard) is None


def test_keeps_what_the_user_copies_during_paste(pasteboard):
    def user_copies():
        pasteboard.clearContents()
        pasteboard.setString_forType_("user", NSPasteboardTypeString)

    paste("new", pasteboard, user_copies, lambda: True)
    assert read(pasteboard) == "user"


def test_without_accessibility_text_stays_on_the_clipboard(pasteboard):
    pressed = []
    assert not paste("new", pasteboard, lambda: pressed.append(1), lambda: False)
    assert read(pasteboard) == "new"
    assert not pressed
