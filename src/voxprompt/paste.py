"""Put text at the cursor through the clipboard, then restore the clipboard."""

import time

from AppKit import NSPasteboard, NSPasteboardItem, NSPasteboardTypeString
from ApplicationServices import AXIsProcessTrusted
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    kCGEventFlagMaskCommand,
    kCGHIDEventTap,
)

V_KEYCODE = 9
RESTORE_DELAY = 0.3  # The target app reads the clipboard after it handles Cmd+V.


def snapshot(pasteboard) -> list:
    items = []
    for item in pasteboard.pasteboardItems() or []:
        copy = NSPasteboardItem.new()
        for kind in item.types():
            data = item.dataForType_(kind)
            if data is not None:
                copy.setData_forType_(data, kind)
        items.append(copy)
    return items


def press_cmd_v() -> None:
    for is_down in (True, False):
        event = CGEventCreateKeyboardEvent(None, V_KEYCODE, is_down)
        CGEventSetFlags(event, kCGEventFlagMaskCommand)
        CGEventPost(kCGHIDEventTap, event)


def paste(text: str, pasteboard=None, press=press_cmd_v, trusted=AXIsProcessTrusted) -> bool:
    """Paste text. Without Accessibility access, leave it on the clipboard and return False."""
    pasteboard = pasteboard or NSPasteboard.generalPasteboard()
    saved = snapshot(pasteboard)
    pasteboard.clearContents()
    pasteboard.setString_forType_(text, NSPasteboardTypeString)
    if not trusted():
        return False

    ours = pasteboard.changeCount()
    press()
    time.sleep(RESTORE_DELAY)
    if pasteboard.changeCount() == ours:  # Otherwise the user copied something new.
        pasteboard.clearContents()
        if saved:
            pasteboard.writeObjects_(saved)
    return True
