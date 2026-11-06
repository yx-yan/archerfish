from metrics import edit_distance, error_rate, normalize


def test_normalize_drops_punctuation_and_case():
    assert normalize("Hello,  World！") == "hello world"


def test_edit_distance():
    assert edit_distance(list("kitten"), list("sitting")) == 3


def test_chinese_uses_characters():
    assert error_rate("帮我看一下", "帮我看下", "zh") == 0.2


def test_english_uses_words():
    assert error_rate("fix this test", "fix the test", "en") == 1 / 3


def test_punctuation_is_not_an_error():
    assert error_rate("你好，世界。", "你好世界", "zh") == 0
