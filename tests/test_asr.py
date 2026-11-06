import wave

import numpy as np
import pytest

from quoth.asr import read_wav


def write_wav(path, rate, samples):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(np.array(samples, dtype=np.int16).tobytes())


def test_read_wav_scales_to_unit_range(tmp_path):
    path = tmp_path / "a.wav"
    write_wav(path, 16_000, [0, 16384, -32768])
    assert read_wav(path).tolist() == [0, 0.5, -1]


def test_read_wav_rejects_other_sample_rates(tmp_path):
    path = tmp_path / "a.wav"
    write_wav(path, 44_100, [0])
    with pytest.raises(ValueError):
        read_wav(path)
