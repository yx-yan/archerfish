from pathlib import Path

import archerfish
from archerfish.dictation import State
from archerfish.overlay import MIN_BAR, SHOW_DELAY, Animation

FRAME = 1 / 30


def run(animation, state, seconds, level=0.0):
    for _ in range(round(seconds / FRAME)):
        animation.step(state, level, FRAME)


def test_quick_press_never_shows():
    animation = Animation()
    run(animation, State.RECORDING, SHOW_DELAY - 2 * FRAME)
    assert animation.done


def test_held_key_shows_the_pill():
    animation = Animation()
    run(animation, State.RECORDING, 0.6)
    assert animation.alpha > 0.9


def test_louder_speech_makes_taller_bars():
    quiet, loud = Animation(), Animation()
    run(quiet, State.RECORDING, 0.6, level=0.1)
    run(loud, State.RECORDING, 0.6, level=1)
    assert sum(loud.bars) > sum(quiet.bars)


def test_working_folds_the_bars_and_blinks_the_cursor():
    animation = Animation()
    run(animation, State.RECORDING, 0.6)
    run(animation, State.WORKING, 0.6)
    assert animation.alpha > 0.9 and animation.merge > 0.9
    seen = set()
    for _ in range(30):
        animation.step(State.WORKING, 0, FRAME)
        seen.add(round(animation.cursor_alpha, 1))
    assert min(seen) < 0.5 < max(seen)


def test_working_after_a_quick_press_stays_hidden():
    animation = Animation()
    run(animation, State.WORKING, 0.6)
    assert animation.done


def test_fades_out_when_ready():
    animation = Animation()
    run(animation, State.RECORDING, 0.6)
    run(animation, State.WORKING, 0.3)
    run(animation, State.READY, 0.6)
    assert animation.done


def test_bars_never_vanish():
    animation = Animation()
    run(animation, State.RECORDING, 2)
    assert min(animation.bars) >= MIN_BAR * 0.99


def test_every_state_has_a_menu_bar_icon():
    icons = Path(archerfish.__file__).parent / "icons"
    names = [state.name.lower() for state in State] + ["warning"]
    assert all((icons / f"{name}.png").exists() for name in names)
