import pytest
from ytmusicapi import exceptions

from yutipy.models import Album, Track
from yutipy.exceptions import InvalidValueException
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

    def get_song(self, track_id):
        return {
            "videoDetails": {
                "videoId": "testvideo1",
                "title": "Test Track Title",
                "lengthSeconds": "215",
                "author": "Test Artist",
            },
            "microformat": {
                "microformatDataRenderer": {
                    "thumbnail": {
                        "thumbnails": [
                            {"url": "https://music.youtube.com/image/track.jpg"}
                        ]
                    },
                    "publishDate": "2026-06-12",
                    "urlCanonical": "https://music.youtube.com/watch?v=testvideo1",
                    "familySafe": True,
                }
            },
            "streamingData": {
                "adaptiveFormats": [
                    {"url": "https://rr1---sn/track.m4a", "loudnessDb": -1.3}
                ]
            },
        }

    def get_album(self, album_id):
        return {
            "artists": [{"id": "artistid1", "name": "Artist One"}],
            "thumbnails": [{"url": "https://music.youtube.com/image/album.jpg"}],
            "duration_seconds": 1234,
            "audioPlaylistId": "playlist1",
            "year": "2026",
            "title": "Test Album",
            "trackCount": 1,
            "tracks": [
                {
                    "artists": [{"id": "artistid1", "name": "Artist One"}],
                    "duration_seconds": 215,
                    "isExplicit": False,
                    "videoId": "testvideo1",
                    "title": "Test Track Title",
                    "trackNumber": 1,
                }
            ],
            "type": "Album",
        }


@pytest.fixture
def mock_ytmusic(monkeypatch, musicyt):
    musicyt.ytmusic = MockYTMusic()


def test_search_valid(musicyt, mock_ytmusic):
    result = musicyt.search("Artist One", "Test Song Title", limit=2)
    assert result is not None
    assert len(result["tracks"]) == 1
    assert len(result["albums"]) == 1
    assert isinstance(result["artists"], list)
    assert isinstance(result["tracks"][0], Track)
    assert result["tracks"][0].title == "Test Song Title"
    assert result["tracks"][0].artists[0].name == "Artist One"
    assert result["tracks"][0].album.title == "Test Album"
    assert result["tracks"][0].album.cover == "https://music.youtube.com/image/test1.jpg"
    assert result["tracks"][0].duration == 210
    assert result["tracks"][0].explicit is False
    assert result["tracks"][0].url == "https://music.youtube.com/watch?v=testvideo1"
    assert isinstance(result["albums"][0], Album)
    assert result["albums"][0].title == "Test Album"
    assert result["albums"][0].artists[0].name == "Artist Two"
    assert result["albums"][0].cover == "https://music.youtube.com/image/test2.jpg"
    assert result["albums"][0].explicit is False
    assert result["albums"][0].url == "https://music.youtube.com/browse/testalbum1"


def test_search_empty_artist(musicyt, mock_ytmusic):
    result = musicyt.search(song="Test Song Title")
    assert result is not None
    assert isinstance(result, dict)


def test_search_empty_song(musicyt, mock_ytmusic):
    result = musicyt.search("Artist One", "")
    assert result is not None
    assert isinstance(result, dict)


def test_search_empty(musicyt, mock_ytmusic):
    with pytest.raises(InvalidValueException):
        musicyt.search("", "")


def test_search_invalid_limit(musicyt):
    with pytest.raises(Exception):
        musicyt.search("Artist One", "Test Song Title", limit=0)
    with pytest.raises(Exception):
        musicyt.search("Artist One", "Test Song Title", limit=100)


def test_get_track_valid(musicyt, mock_ytmusic):
    result = musicyt.get_track("testvideo1")

    assert result is not None
    assert result.id == "testvideo1"
    assert result.title == "Test Track Title"
    assert result.duration == 215
    assert result.preview_url == "https://rr1---sn/track.m4a"
    assert result.release_date == "2026-06-12"
    assert result.explicit is False
    assert result.artists[0].name == "Test Artist"
    assert result.album.cover == "https://music.youtube.com/image/track.jpg"
    assert result.url == "https://music.youtube.com/watch?v=testvideo1"


def test_get_album_valid(musicyt, mock_ytmusic):
    result = musicyt.get_album("playlist1")

    assert result is not None
    assert result.id == "playlist1"
    assert result.title == "Test Album"
    assert result.release_date == "2026"
    assert result.total_tracks == 1
    assert result.duration == 1234
    assert result.cover == "https://music.youtube.com/image/album.jpg"
    assert result.url == "https://music.youtube.com/playlist?list=playlist1"
    assert result.artists[0].name == "Artist One"
    assert len(result.tracks) == 1
    assert result.tracks[0].title == "Test Track Title"
    assert result.tracks[0].track_number == 1
    assert result.tracks[0].service_name == "YouTube Music"


def test_get_track_handles_server_error(musicyt, monkeypatch):
    def raise_error(track_id):
        raise exceptions.YTMusicServerError("Server error")

    monkeypatch.setattr(musicyt.ytmusic, "get_song", raise_error)

    result = musicyt.get_track("bad")

    assert result is None
