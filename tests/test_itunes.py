import pytest

from tests import BaseResponse
from yutipy.exceptions import InvalidValueException
from yutipy.itunes import Itunes


@pytest.fixture
def itunes():
    return Itunes()


class MockResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "results": [
                {
                    "wrapperType": "track",
                    "kind": "song",
                    "artistId": 1,
                    "collectionId": 2,
                    "trackId": 3,
                    "artistName": "Artist One",
                    "collectionName": "Album Alpha",
                    "trackName": "Song X",
                    "collectionViewUrl": "https://music.apple.com/album/2",
                    "trackViewUrl": "https://music.apple.com/track/3",
                    "artworkUrl100": "https://music.apple.com/image/cover.jpg",
                    "trackCount": 10,
                    "releaseDate": "2020-01-01T12:00:00Z",
                    "primaryGenreName": "Pop",
                    "trackTimeMillis": 123000,
                    "collectionExplicitness": "notExplicit",
                    "trackExplicitness": "notExplicit",
                    "artistViewUrl": "https://music.apple.com/artist/1",
                    "previewUrl": "https://music.apple.com/preview.mp3",
                },
                {
                    "wrapperType": "collection",
                    "artistId": 2,
                    "collectionId": 4,
                    "artistName": "Artist Two",
                    "collectionName": "Album Beta",
                    "collectionViewUrl": "https://music.apple.com/album/4",
                    "artworkUrl100": "https://music.apple.com/image/cover2.jpg",
                    "trackCount": 8,
                    "releaseDate": "2021-02-02T12:00:00Z",
                    "primaryGenreName": "Rock",
                    "collectionExplicitness": "notExplicit",
                    "artistViewUrl": "https://music.apple.com/artist/2",
                },
            ]
        }


@pytest.fixture
def mock_response(itunes, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(itunes._session, "get", mock_get)


def test_search(itunes, mock_response):
    result = itunes.search("Artist One", "Song X", limit=2)
    assert result is not None
    assert len(result) == 2
    assert result[0].title == "Song X"
    assert result[0].album.title == "Album Alpha"
    assert result[1].title == "Album Beta"
    assert result[1].artists[0].name == "Artist Two"


def test_search_empty_artist(itunes, mock_response):
    result = itunes.search(song="Song X", limit=2)
    assert result is not None


def test_search_empty_song(itunes, mock_response):
    result = itunes.search(artist="Artist Two", limit=2)
    assert result is not None


def test_search_empty(itunes, mock_response):
    with pytest.raises(InvalidValueException):
        itunes.search("", "")


def test_close_session(itunes):
    itunes.close_session()
    assert itunes.is_session_closed
