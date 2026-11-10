"""Menu bar app: hold the right Option key to dictate a prompt."""

import os
import signal
import threading
from pathlib import Path

import rumps
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
from ApplicationServices import AXIsProcessTrustedWithOptions
from dotenv import load_dotenv
from Quartz import CGRequestListenEventAccess

from archerfish.asr import QwenTranscriber
from archerfish.dictation import Dictation, State
from archerfish.hotkey import HoldKey
from archerfish.onboarding import SetupWindow, incomplete
from archerfish.overlay import Overlay
from archerfish.paste import paste
from archerfish.recorder import Microphone
from archerfish.rewrite import Rewriter

ICON_DIR = Path(__file__).parent / "icons"
ICONS = {state: str(ICON_DIR / f"{state.name.lower()}.png") for state in State}
WARNING_ICON = str(ICON_DIR / "warning.png")


class MenuBar(rumps.App):
    def __init__(self, dictation: Dictation, hold_key: HoldKey):
        super().__init__("archerfish", icon=ICONS[State.LOADING], template=True, quit_button=None)
        self.dictation = dictation
        self.hold_key = hold_key
        self.overlay = Overlay(dictation)
        self.setup = SetupWindow()
        self.greeted = False
        self.status = rumps.MenuItem(State.LOADING.value)
        self.menu = [
            self.status,
            rumps.separator,
            rumps.MenuItem("Setup...", callback=lambda _: self.setup.show()),
            rumps.MenuItem("Quit Archerfish", callback=lambda _: quit_now()),
        ]

    @rumps.timer(0.1)
    def refresh(self, _):
        """Update the UI here because AppKit must only be touched on the main thread."""
        state, message = self.dictation.state, self.dictation.message
        icon = WARNING_ICON if state is State.READY and message else ICONS[state]
        if icon != self.icon:
            self.icon = icon
        self.status.title = message or state.value
        self.overlay.update()
        if not self.greeted:
            self.greeted = True
            if incomplete():
                self.setup.show()

    @rumps.timer(2)
    def listen(self, _):
        """Keep trying, so the app can show what is missing instead of exiting."""
        if self.hold_key.tap is not None:
            return
        try:
            self.hold_key.start()
            self.dictation.message = ""
        except PermissionError:
            self.dictation.message = "Allow Input Monitoring in Setup, then reopen Archerfish"


def quit_now(*_) -> None:
    os._exit(0)  # Skip closing the stream, which is where CoreAudio can deadlock.


def main() -> None:
    load_dotenv()
    AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True})
    CGRequestListenEventAccess()

    dictation = Dictation(Microphone(), QwenTranscriber, Rewriter(), paste)
    hold_key = HoldKey(dictation.press, dictation.release)

    signal.signal(signal.SIGINT, quit_now)
    threading.Thread(target=dictation.run, daemon=True).start()
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    MenuBar(dictation, hold_key).run()


if __name__ == "__main__":
    main()
