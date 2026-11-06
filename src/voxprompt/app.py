"""Menu bar app: hold the right Option key to dictate a prompt."""

import os
import signal
import threading

import rumps
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
from ApplicationServices import AXIsProcessTrustedWithOptions
from dotenv import load_dotenv
from Quartz import CGRequestListenEventAccess

from voxprompt.asr import QwenTranscriber
from voxprompt.dictation import Dictation, State
from voxprompt.hotkey import HoldKey
from voxprompt.paste import paste
from voxprompt.recorder import Microphone
from voxprompt.rewrite import Rewriter

ICONS = {
    State.LOADING: "⏳",
    State.READY: "🎙️",
    State.RECORDING: "🔴",
    State.WORKING: "💭",
}


class MenuBar(rumps.App):
    def __init__(self, dictation: Dictation, hold_key: HoldKey):
        super().__init__("voxprompt", title=ICONS[State.LOADING], quit_button=None)
        self.dictation = dictation
        self.hold_key = hold_key
        self.status = rumps.MenuItem(State.LOADING.value)
        self.menu = [self.status, rumps.MenuItem("Quit", callback=lambda _: quit_now())]

    @rumps.timer(0.1)
    def refresh(self, _):
        """Update the UI here because AppKit must only be touched on the main thread."""
        state, message = self.dictation.state, self.dictation.message
        self.title = "⚠️" if state is State.READY and message else ICONS[state]
        self.status.title = message or state.value

    @rumps.timer(2)
    def listen(self, _):
        """Keep trying, so the app can show what is missing instead of exiting."""
        if self.hold_key.tap is not None:
            return
        try:
            self.hold_key.start()
            self.dictation.message = ""
        except PermissionError:
            self.dictation.message = "Allow Input Monitoring, then reopen the app"


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
