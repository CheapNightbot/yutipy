import pytest

from yutipy.exceptions import SpotifyException
from yutipy.models import MusicInfo
from yutipy.spotify import Spotify


@pytest.fixture(scope="module")
def spotify():
    try:
        return Spotify()
    except SpotifyException:
        pytest.skip("Spotify credentials not found")


def test_search(spotify):
    artist = "Adele"
    song = "Hello"
    result = spotify.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert result.title == song
    assert artist in result.artists


def test_search_advanced_with_isrc(spotify):
    artist = "Adele"
    song = "Hello"
    isrc = "GBBKS1500214"
    result = spotify.search_advanced(artist, song, isrc=isrc)
    assert result is not None
    assert result.isrc == isrc


def test_search_advanced_with_upc(spotify):
    artist = "Miles Davis"
    album = "Kind Of Blue (Legacy Edition)"
    upc = "888880696069"
    result = spotify.search_advanced(artist, album, upc=upc)
    print(result)
    assert result is not None


def test_get_artists_ids(spotify):
    artist = "Adele"
    artist_ids = spotify._get_artists_ids(artist)
    assert isinstance(artist_ids, list)
    assert len(artist_ids) > 0


def test_close_session(spotify):
    spotify.close_session()
    assert spotify.is_session_closed
