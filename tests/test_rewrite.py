from types import SimpleNamespace
from unittest.mock import MagicMock

from openai import APITimeoutError

from quoth.rewrite import Rewriter


def client_returning(content):
    client = MagicMock()
    message = SimpleNamespace(content=content)
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )
    return client


def test_returns_cleaned_text():
    result = Rewriter(client_returning("  Fix the test.  ")).rewrite("um fix the test")
    assert (result.text, result.fell_back) == ("Fix the test.", False)


def test_falls_back_on_timeout():
    client = MagicMock()
    client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
    result = Rewriter(client).rewrite("raw text")
    assert (result.text, result.fell_back) == ("raw text", True)


def test_falls_back_on_empty_reply():
    result = Rewriter(client_returning("")).rewrite("raw text")
    assert (result.text, result.fell_back) == ("raw text", True)
