import pytest

from yutipy.deezer import Deezer
from yutipy.models import MusicInfo


@pytest.fixture
def deezer():
    return Deezer()


def test_search_valid(deezer):
    result = deezer.search("Adele", "Hello")
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert result.title == "Hello"


def test_search_invalid(deezer):
    result = deezer.search("Nonexistent Artist", "Nonexistent Song")
    assert result is None


def test_get_upc_isrc_track(deezer):
    track_id = 781592622
    result = deezer._get_upc_isrc(track_id, "track")
    assert result is not None
    assert "isrc" in result
    assert "release_date" in result


def test_get_upc_isrc_album(deezer):
    album_id = 115888392
    result = deezer._get_upc_isrc(album_id, "album")
    assert result is not None
    assert "upc" in result
    assert "release_date" in result


def test_search_no_results(deezer):
    result = deezer.search("Adele", "Nonexistent Song")
    assert result is None


def test_close_session(deezer):
    deezer.close_session()
    assert deezer.is_session_closed
