import numpy as np

from quoth.recorder import loudness, is_silent


def test_all_zero_audio_is_silent():
    assert is_silent(np.zeros(100, dtype=np.int16))


def test_faint_noise_is_not_silent():
    samples = np.zeros(100, dtype=np.int16)
    samples[50] = 1
    assert not is_silent(samples)


def test_loudness_is_zero_for_silence():
    assert loudness(np.zeros((160, 1), dtype=np.int16)) == 0


def test_loudness_rises_with_volume_and_stays_in_range():
    quiet = loudness(np.full((160, 1), 300, dtype=np.int16))
    loud = loudness(np.full((160, 1), 3000, dtype=np.int16))
    assert 0 < quiet < loud <= 1
    assert loudness(np.full((160, 1), 32000, dtype=np.int16)) == 1
