import pytest
from pytest import raises

from yutipy.itunes import Itunes
from yutipy.models import MusicInfo
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def itunes():
    return Itunes()


def test_search_valid(itunes):
    artist = "Adele"
    song = "Hello"
    result = itunes.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert "Hello" in result.title
    assert "Adele" in result.artists


def test_search_invalid(itunes):
    artist = "Nonexistent Artist"
    song = "Nonexistent Song"
    result = itunes.search(artist, song)
    assert result is None


def test_search_empty_artist(itunes):
    artist = ""
    song = "Hello"

    with raises(InvalidValueException):
        itunes.search(artist, song)


def test_search_empty_song(itunes):
    artist = "Adele"
    song = ""

    with raises(InvalidValueException):
        itunes.search(artist, song)


def test_close_session(itunes):
    itunes.close_session()
    assert itunes.is_session_closed
