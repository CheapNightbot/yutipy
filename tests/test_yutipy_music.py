import pytest
from yutipy.yutipy_music import YutipyMusic
from yutipy.models import MusicInfos
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def yutipy_music():
    return YutipyMusic()


def test_search_valid(yutipy_music):
    artist = "Adele"
    song = "Hello"
    result = yutipy_music.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfos)
    assert "Hello" in result.title
    assert "Adele" in result.artists


def test_search_invalid(yutipy_music):
    artist = "Nonexistent Artist"
    song = "Nonexistent Song"
    result = yutipy_music.search(artist, song)
    assert result is None


def test_search_empty_artist(yutipy_music):
    artist = ""
    song = "Hello"

    with pytest.raises(InvalidValueException):
        yutipy_music.search(artist, song)


def test_search_empty_song(yutipy_music):
    artist = "Adele"
    song = ""

    with pytest.raises(InvalidValueException):
        yutipy_music.search(artist, song)


def test_close_sessions(yutipy_music):
    yutipy_music.close_sessions()
    for service in yutipy_music.services.values():
        assert service.is_session_closed
