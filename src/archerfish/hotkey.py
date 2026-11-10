"""Global hold-to-talk key."""

from collections.abc import Callable

from Quartz import (
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    CGEventMaskBit,
    CGEventTapCreate,
    CGEventTapEnable,
    kCFRunLoopCommonModes,
    kCGEventFlagsChanged,
    kCGEventTapDisabledByTimeout,
    kCGEventTapDisabledByUserInput,
    kCGEventTapOptionListenOnly,
    kCGHeadInsertEventTap,
    kCGKeyboardEventKeycode,
    kCGSessionEventTap,
)

RIGHT_OPTION_KEYCODE = 61
RIGHT_OPTION_FLAG = 0x40  # NX_DEVICERALTKEYMASK: set only while the right Option is down.


class HoldKey:
    def __init__(self, on_press: Callable[[], None], on_release: Callable[[], None]):
        self.on_press = on_press
        self.on_release = on_release
        self.down = False
        self.tap = None

    def start(self) -> None:
        """Listen on the current thread's run loop."""
        self.tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            CGEventMaskBit(kCGEventFlagsChanged),
            self._on_event,
            None,
        )
        if self.tap is None:
            raise PermissionError("Input Monitoring access is required")
        source = CFMachPortCreateRunLoopSource(None, self.tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)
        CGEventTapEnable(self.tap, True)

    def _on_event(self, _proxy, event_type, event, _refcon):
        if event_type in (kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput):
            CGEventTapEnable(self.tap, True)
        elif CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode) == RIGHT_OPTION_KEYCODE:
            self.update(bool(CGEventGetFlags(event) & RIGHT_OPTION_FLAG))
        return event

    def update(self, is_down: bool) -> None:
        if is_down != self.down:
            self.down = is_down
            (self.on_press if is_down else self.on_release)()
