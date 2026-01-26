import pytest

from yutipy.models import Album, Track
from yutipy.musicyt import MusicYT


@pytest.fixture
def musicyt():
    return MusicYT()


class MockYTMusic:
    def search(self, *args, **kwargs):
        return [
            {
                "category": "Top result",
                "resultType": "video",
                "videoId": "testvideo1",
                "title": "Test Song Title",
                "artists": [{"name": "Artist One", "id": "artistid1"}],
                "duration_seconds": 210,
                "isExplicit": False,
                "thumbnails": [
                    {
                        "url": "https://music.youtube.com/image/test1.jpg",
                        "width": 400,
                        "height": 225,
                    }
                ],
                "album": "Test Album",
            },
            {
                "category": "Top result",
                "resultType": "album",
                "browseId": "testalbum1",
                "title": "Test Album",
                "type": "Album",
                "artists": [{"name": "Artist Two", "id": "artistid2"}],
                "isExplicit": False,
                "thumbnails": [
                    {
                        "url": "https://music.youtube.com/image/test2.jpg",
                        "width": 120,
                        "height": 120,
                    }
                ],
            },
        ]


@pytest.fixture
def mock_ytmusic(monkeypatch, musicyt):
    musicyt.ytmusic = MockYTMusic()


def test_search_valid(musicyt, mock_ytmusic):
    result = musicyt.search("Artist One", "Test Song Title", limit=2)
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[0], Track)
    assert result[0].title == "Test Song Title"
    assert result[0].artists[0].name == "Artist One"
    assert result[0].album.title == "Test Album"
    assert result[0].album.cover == "https://music.youtube.com/image/test1.jpg"
    assert result[0].duration == 210
    assert result[0].explicit is False
    assert result[0].url == "https://music.youtube.com/watch?v=testvideo1"
    assert isinstance(result[1], Album)
    assert result[1].title == "Test Album"
    assert result[1].artists[0].name == "Artist Two"
    assert result[1].cover == "https://music.youtube.com/image/test2.jpg"
    assert result[1].explicit is False
    assert result[1].url == "https://music.youtube.com/browse/testalbum1"


def test_search_invalid_artist(musicyt):
    with pytest.raises(Exception):
        musicyt.search("", "Test Song Title")


def test_search_invalid_song(musicyt):
    with pytest.raises(Exception):
        musicyt.search("Artist One", "")


def test_search_invalid_limit(musicyt):
    with pytest.raises(Exception):
        musicyt.search("Artist One", "Test Song Title", limit=0)
    with pytest.raises(Exception):
        musicyt.search("Artist One", "Test Song Title", limit=100)
