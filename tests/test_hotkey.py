from archerfish.hotkey import HoldKey


def make_key():
    events = []
    return HoldKey(lambda: events.append("press"), lambda: events.append("release")), events


def test_press_and_release_fire_once_each():
    key, events = make_key()
    for is_down in (True, True, False, False):
        key.update(is_down)
    assert events == ["press", "release"]
