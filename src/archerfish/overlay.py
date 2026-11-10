"""A floating pill that shows the waveform while recording and a cursor while working."""

import math
import time

import rumps
from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSGradient,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSStatusWindowLevel,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorIgnoresCycle,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)

from archerfish.dictation import State

WIDTH, HEIGHT = 92, 40
BOTTOM_MARGIN = 48
FRAME = 1 / 30
SHOW_DELAY = 0.15  # Quick Option shortcuts should not flash the pill.

BAR_WIDTH, BAR_STEP = 5, 12
CURSOR_HEIGHT = 26
SHAPE = (0.55, 0.85, 1, 0.7)  # Tallest bar heights, relative to the cursor.
MIN_BAR = 0.16
BLINK_SECONDS = 0.9


def approach(value: float, target: float, rate: float, dt: float) -> float:
    return value + (target - value) * min(1, rate * dt)


class Animation:
    """What the pill looks like. Kept free of AppKit so it can be tested."""

    def __init__(self):
        self.alpha = 0.0
        self.bars = [MIN_BAR] * len(SHAPE)
        self.merge = 0.0  # 0 is the waveform; 1 is the bars folded into the cursor.
        self.cursor_alpha = 1.0
        self.held = 0.0
        self.clock = 0.0

    def step(self, state: State, level: float, dt: float) -> None:
        self.clock += dt
        self.held = self.held + dt if state is State.RECORDING else 0
        recording = state is State.RECORDING and self.held >= SHOW_DELAY
        working = state is State.WORKING and self.alpha > 0

        self.alpha = approach(self.alpha, 1 if recording or working else 0, 14, dt)
        self.merge = approach(self.merge, 1 if working else 0, 10, dt)
        for index, shape in enumerate(SHAPE):
            wobble = 0.7 + 0.3 * math.sin(self.clock * 11 + index * 1.7)
            target = MIN_BAR + (shape - MIN_BAR) * level * wobble
            rate = 30 if target > self.bars[index] else 12  # Jump up, settle down.
            self.bars[index] = approach(self.bars[index], target, rate, dt)

        blink = 0.5 + 0.5 * math.cos(self.clock * math.tau / BLINK_SECONDS)
        self.cursor_alpha = 0.35 + 0.65 * blink if working else 1

    @property
    def done(self) -> bool:
        return self.alpha < 0.01


def color(hex_value: int, alpha: float = 1) -> NSColor:
    red, green, blue = (hex_value >> 16 & 255, hex_value >> 8 & 255, hex_value & 255)
    return NSColor.colorWithSRGBRed_green_blue_alpha_(red / 255, green / 255, blue / 255, alpha)


def draw_bar(x: float, height: float, fill: NSColor) -> None:
    rect = NSMakeRect(x - BAR_WIDTH / 2, (HEIGHT - height) / 2, BAR_WIDTH, height)
    fill.setFill()
    NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, BAR_WIDTH / 2, BAR_WIDTH / 2).fill()


class PillView(NSView):
    def isOpaque(self):
        return False

    def drawRect_(self, _):
        pill = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(0, 0, WIDTH, HEIGHT), HEIGHT / 2, HEIGHT / 2
        )
        NSGradient.alloc().initWithStartingColor_endingColor_(
            color(0x2B2D42), color(0x14151F)
        ).drawInBezierPath_angle_(pill, -90)

        animation = self.animation
        center = WIDTH / 2
        left = center - BAR_STEP * 2
        for index, height in enumerate(animation.bars):
            x = left + BAR_STEP * index
            draw_bar(
                x + (center - x) * animation.merge,
                height * CURSOR_HEIGHT,
                color(0xF4F1EA, 1 - animation.merge),
            )
        x = left + BAR_STEP * len(animation.bars)
        draw_bar(
            x + (center - x) * animation.merge,
            CURSOR_HEIGHT,
            color(0xFFB020, animation.cursor_alpha),
        )


class Overlay:
    def __init__(self, dictation):
        self.dictation = dictation
        self.animation = Animation()
        self.last_frame = 0.0
        self.timer = rumps.Timer(self.tick, FRAME)

        # A nonactivating panel never takes focus, so the paste still reaches the text box.
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WIDTH, HEIGHT),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setOpaque_(False)
        self.panel.setHasShadow_(True)
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setLevel_(NSStatusWindowLevel)
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
        )
        self.view = PillView.alloc().initWithFrame_(NSMakeRect(0, 0, WIDTH, HEIGHT))
        self.view.animation = self.animation
        self.panel.setContentView_(self.view)

    def update(self) -> None:
        """Start animating when a recording begins. The timer only runs while it is needed."""
        if self.dictation.state is State.RECORDING and not self.timer.is_alive():
            self.last_frame = time.monotonic()
            self.timer.start()

    def tick(self, _) -> None:
        now = time.monotonic()
        dt, self.last_frame = now - self.last_frame, now
        was_visible = self.panel.isVisible()
        state = self.dictation.state
        self.animation.step(state, self.dictation.mic.level, dt)

        if self.animation.done:
            if was_visible:
                self.panel.orderOut_(None)
            if state is not State.RECORDING:
                self.timer.stop()
            return
        if not was_visible:
            self.place()
            self.panel.orderFrontRegardless()
        self.panel.setAlphaValue_(self.animation.alpha)
        self.view.setNeedsDisplay_(True)

    def place(self) -> None:
        frame = NSScreen.mainScreen().visibleFrame()
        x = frame.origin.x + (frame.size.width - WIDTH) / 2
        self.panel.setFrameOrigin_((x, frame.origin.y + BOTTOM_MARGIN))
