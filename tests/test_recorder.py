import numpy as np

from quoth.recorder import is_silent


def test_all_zero_audio_is_silent():
    assert is_silent(np.zeros(100, dtype=np.int16))


def test_faint_noise_is_not_silent():
    samples = np.zeros(100, dtype=np.int16)
    samples[50] = 1
    assert not is_silent(samples)
