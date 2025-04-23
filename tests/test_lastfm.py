import pytest

from yutipy.lastfm import LastFm
from yutipy.models import UserPlaying
from tests import BaseResponse


@pytest.fixture
def lastfm():
    return LastFm(api_key="test_api_key")


class MockResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "recenttracks": {
                "track": [
                    {
                        "artist": {"mbid": "", "#text": "Test Artist"},
                        "image": [
                            {
                                "size": "small",
                                "#text": "https://example.com/image/small.jpg",
                            },
                            {
                                "size": "extralarge",
                                "#text": "https://example.com/image/extralarge.jpg",
                            },
                        ],
                        "mbid": "",
                        "album": {
                            "mbid": "",
                            "#text": "Test Album",
                        },
                        "name": "Test Track",
                        "url": "https://www.last.fm/music/test+track",
                    }
                ]
            }
        }


@pytest.fixture
def mock_response(lastfm, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(lastfm._LastFm__session, "get", mock_get)


def test_get_currently_playing(lastfm, mock_response):
    username = "bob"
    currently_playing = lastfm.get_currently_playing(username=username)
    assert currently_playing is not None
    assert isinstance(currently_playing, UserPlaying)
    assert currently_playing.title == "Test Track"
    assert currently_playing.album_title == "Test Album"
    assert "extralarge" in currently_playing.album_art
    assert currently_playing.is_playing is False
