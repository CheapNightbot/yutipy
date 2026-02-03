import pytest
from pytest import raises

from tests import BaseResponse
from yutipy.exceptions import InvalidValueException
from yutipy.kkbox import KKBox
from yutipy.models import Album, Track


@pytest.fixture(scope="module")
def kkbox():
    def mock_get_access_token():
        return {
            "access_token": "test_access_token",
            "expires_in": 3600,
            "requested_at": 1234567890,
        }

    kkbox_instance = KKBox(
        client_id="test_client_id", client_secret="test_client_secret", defer_load=True
    )
    kkbox_instance._get_access_token = mock_get_access_token
    kkbox_instance.load_token_after_init()
    return kkbox_instance


class MockSearchResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "tracks": {
                "data": [
                    {
                        "id": "track123",
                        "name": "Test Track",
                        "isrc": "ISRC123",
                        "url": "https://www.kkbox.com/sg/en/song/track123",
                        "duration": 200000,
                        "track_number": 1,
                        "explicitness": False,
                        "album": {
                            "id": "album123",
                            "name": "Test Album",
                            "url": "https://www.kkbox.com/sg/en/album/album123",
                            "release_date": "2020-01-01",
                            "explicitness": False,
                            "images": [
                                {"url": "https://www.kkbox.com/image/album123_160.jpg"},
                                {"url": "https://www.kkbox.com/image/album123_500.jpg"},
                                {
                                    "url": "https://www.kkbox.com/image/album123_1000.jpg"
                                },
                            ],
                            "artist": {
                                "id": "artist123",
                                "name": "Artist One",
                                "url": "https://www.kkbox.com/sg/en/artist/artist123",
                                "images": [
                                    {
                                        "url": "https://www.kkbox.com/image/artist123_160.jpg"
                                    },
                                    {
                                        "url": "https://www.kkbox.com/image/artist123_300.jpg"
                                    },
                                ],
                            },
                        },
                    }
                ]
            },
            "albums": {
                "data": [
                    {
                        "id": "album123",
                        "name": "Test Album",
                        "url": "https://www.kkbox.com/sg/en/album/album123",
                        "release_date": "2020-01-01",
                        "explicitness": False,
                        "images": [
                            {"url": "https://www.kkbox.com/image/album123_160.jpg"},
                            {"url": "https://www.kkbox.com/image/album123_500.jpg"},
                            {"url": "https://www.kkbox.com/image/album123_1000.jpg"},
                        ],
                        "artist": {
                            "id": "artist123",
                            "name": "Artist One",
                            "url": "https://www.kkbox.com/sg/en/artist/artist123",
                            "images": [
                                {
                                    "url": "https://www.kkbox.com/image/artist123_160.jpg"
                                },
                                {
                                    "url": "https://www.kkbox.com/image/artist123_300.jpg"
                                },
                            ],
                        },
                    }
                ]
            },
        }


class MockTrackResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "id": "track123",
            "name": "Test Track",
            "url": "https://www.kkbox.com/sg/en/song/track123",
            "track_number": 1,
            "explicitness": False,
            "duration": 200000,
            "isrc": "ISRC123",
            "album": {
                "id": "album123",
                "name": "Test Album",
                "url": "https://www.kkbox.com/sg/en/album/album123",
                "release_date": "2020-01-01",
                "explicitness": False,
                "images": [
                    {"url": "https://www.kkbox.com/image/album123_160.jpg"},
                    {"url": "https://www.kkbox.com/image/album123_500.jpg"},
                    {"url": "https://www.kkbox.com/image/album123_1000.jpg"},
                ],
                "artist": {
                    "id": "artist123",
                    "name": "Artist One",
                    "url": "https://www.kkbox.com/sg/en/artist/artist123",
                    "images": [
                        {"url": "https://www.kkbox.com/image/artist123_160.jpg"},
                        {"url": "https://www.kkbox.com/image/artist123_300.jpg"},
                    ],
                },
            },
        }


class MockAlbumResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "id": "album123",
            "name": "Test Album",
            "url": "https://www.kkbox.com/sg/en/album/album123",
            "release_date": "2020-01-01",
            "explicitness": False,
            "images": [
                {"url": "https://www.kkbox.com/image/album123_160.jpg"},
                {"url": "https://www.kkbox.com/image/album123_500.jpg"},
                {"url": "https://www.kkbox.com/image/album123_1000.jpg"},
            ],
            "artist": {
                "id": "artist123",
                "name": "Artist One",
                "url": "https://www.kkbox.com/sg/en/artist/artist123",
                "images": [
                    {"url": "https://www.kkbox.com/image/artist123_160.jpg"},
                    {"url": "https://www.kkbox.com/image/artist123_300.jpg"},
                ],
            },
        }


@pytest.fixture
def mock_search_response(kkbox, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockSearchResponse()

    monkeypatch.setattr(kkbox._session, "get", mock_get)


@pytest.fixture
def mock_track_response(kkbox, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockTrackResponse()

    monkeypatch.setattr(kkbox._session, "get", mock_get)


@pytest.fixture
def mock_album_response(kkbox, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockAlbumResponse()

    monkeypatch.setattr(kkbox._session, "get", mock_get)


def test_search_valid(kkbox, mock_search_response):
    result = kkbox.search("Artist One", "Test Track")
    assert result is not None
    assert any(isinstance(x, Track) for x in result)
    assert any(isinstance(x, Album) for x in result)
    assert result[0].title == "Test Track"
    assert result[1].title == "Test Album"


def test_search_empty_artist(kkbox, mock_search_response):
    result = kkbox.search(song="Test Track")
    assert result is not None


def test_search_empty_song(kkbox, mock_search_response):
    result = kkbox.search(artist="Artist one")
    assert result is not None


def test_search_empty(kkbox, mock_search_response):
    with pytest.raises(InvalidValueException):
        kkbox.search("", "")


def test_get_track(kkbox, mock_track_response):
    result = kkbox.get_track("track123")
    assert result is not None
    assert isinstance(result, Track)
    assert result.title == "Test Track"
    assert result.album.title == "Test Album"
    assert result.artists[0].name == "Artist One"


def test_get_album(kkbox, mock_album_response):
    result = kkbox.get_album("album123")
    assert result is not None
    assert isinstance(result, Album)
    assert result.title == "Test Album"
    assert result.artists[0].name == "Artist One"


def test_get_html_widget(kkbox):
    html_widget = kkbox.get_html_widget(id="album123", content_type="album")
    assert html_widget is not None
    assert isinstance(html_widget, str)

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="album123", content_type="track")

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="album123", content_type="album", territory="US")

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="album123", content_type="album", widget_lang="JP")


def test_close_session(kkbox):
    kkbox.close_session()
    assert kkbox.is_session_closed
