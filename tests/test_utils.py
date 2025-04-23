import pytest
from yutipy.utils import are_strings_similar, separate_artists


def test_are_strings_similar():
    assert are_strings_similar("Hello World", "Hello World", use_translation=False) is True
    assert are_strings_similar("Hello World", "Hello", use_translation=False) is True


def test_are_strings_similar_translation():
    assert are_strings_similar("ポーター", "Porter") is True


def test_separate_artists():
    assert separate_artists("Artist A & Artist B") == ["Artist A", "Artist B"]
    assert separate_artists("Artist A ft. Artist B") == ["Artist A", "Artist B"]
    assert separate_artists("Artist A") == ["Artist A"]
    assert separate_artists("Artist A and Artist B") == ["Artist A", "Artist B"]
    assert separate_artists("Artist A / Artist B") == ["Artist A", "Artist B"]
    assert separate_artists("Artist A, Artist B", custom_separator=",") == [
        "Artist A",
        "Artist B",
    ]
