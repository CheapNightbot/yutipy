import pytest
from pytest import raises
from yutipy.musicyt import MusicYT
from yutipy.models import MusicInfo
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def music_yt():
    return MusicYT()


def test_search_valid(music_yt):
    artist = "Adele"
    song = "Hello (Official Music Video)"
    result = music_yt.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert artist in result.artists
    assert result.title == song


def test_search_invalid(music_yt):
    artist = ";laksjdflkajsdfj;asdjf"
    song = "jaksjd;fljkas;dfkjasldkjf"
    result = music_yt.search(artist, song)
    assert result is None


def test_search_partial_match(music_yt):
    artist = "Adele"
    song = "Hello"
    result = music_yt.search(artist, song)
    assert result is not None
    assert "Hello" in result.title  # Assuming the title contains the song name


def test_search_empty_artist(music_yt):
    artist = ""
    song = "Hello"

    with raises(InvalidValueException):
        music_yt.search(artist, song)


def test_search_empty_song(music_yt):
    artist = "Adele"
    song = ""

    with raises(InvalidValueException):
        music_yt.search(artist, song)
