import pytest

from tests import BaseResponse
from yutipy.lastfm import LastFm


@pytest.fixture
def lastfm():
    return LastFm(api_key="test_api_key")


class MockProfileResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "user": {
                "name": "user123",
                "realname": "User One",
                "type": "user",
                "url": "https://www.last.fm/user/user123",
                "image": [
                    {
                        "size": "small",
                        "#text": "https://lastfm.freetls.fastly.net/i/u/34s/test.png",
                    },
                    {
                        "size": "extralarge",
                        "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/test.png",
                    },
                ],
            }
        }


class MockCurrentlyPlayingResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "artist": {"mbid": "", "#text": "Artist X"},
            "album": {"mbid": "", "#text": "Album Y"},
            "name": "Track Z",
            "url": "https://www.last.fm/music/Artist+X/_/Track+Z",
            "image": [
                {
                    "size": "small",
                    "#text": "https://lastfm.freetls.fastly.net/i/u/34s/test.jpg",
                },
                {
                    "size": "extralarge",
                    "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/test.jpg",
                },
            ],
            "@attr": {"nowplaying": "true"},
        }


class MockLastPlayedResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "artist": {"mbid": "", "#text": "Artist Y"},
            "album": {"mbid": "", "#text": "Album X"},
            "name": "Track Q",
            "url": "https://www.last.fm/music/Artist+Y/_/Track+Q",
            "image": [
                {
                    "size": "small",
                    "#text": "https://lastfm.freetls.fastly.net/i/u/34s/test2.jpg",
                },
                {
                    "size": "extralarge",
                    "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/test2.jpg",
                },
            ],
            "date": {"uts": "1769322583", "#text": "25 Jan 2026, 06:29"},
        }


def test_get_user_profile(lastfm, monkeypatch):
    monkeypatch.setattr(lastfm._session, "get", lambda *a, **kw: MockProfileResponse())
    result = lastfm.get_user_profile("user123")
    assert result is not None
    assert result["username"] == "user123"
    assert result["name"] == "User One"
    assert result["account_type"] == "user"
    assert result["avatar"].endswith("test.png")
    assert result["url"] == "https://www.last.fm/user/user123"


def test_get_currently_playing(lastfm, monkeypatch):
    monkeypatch.setattr(
        lastfm._session, "get", lambda *a, **kw: MockCurrentlyPlayingResponse()
    )
    result = lastfm.get_currently_playing("user123")
    assert result is not None
    assert result["scrobbling_now"] is True
    assert result["artist"] == "Artist X"
    assert result["album"] == "Album Y"
    assert result["title"] == "Track Z"
    assert result["cover"].endswith("test.jpg")
    assert result["url"] == "https://www.last.fm/music/Artist+X/_/Track+Z"


def test_get_last_played(lastfm, monkeypatch):
    monkeypatch.setattr(
        lastfm._session, "get", lambda *a, **kw: MockLastPlayedResponse()
    )
    result = lastfm.get_currently_playing("user123")
    assert result is not None
    assert result["scrobbling_now"] is False
    assert result["artist"] == "Artist Y"
    assert result["album"] == "Album X"
    assert result["title"] == "Track Q"
    assert result["cover"].endswith("test2.jpg")
    assert result["url"] == "https://www.last.fm/music/Artist+Y/_/Track+Q"
    assert result["last_played_utc"]["unix_timestamp"] == "1769322583"
    assert result["last_played_utc"]["datetime"] == "25 Jan 2026, 06:29"
