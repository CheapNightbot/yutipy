import pytest

from yutipy.deezer import Deezer
from tests import BaseResponse


@pytest.fixture
def deezer():
    return Deezer()


class MockSearchResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "data": [
                {
                    "id": "123456",
                    "title": "Test Song Title (Extended Version)",
                    "link": "https://www.deezer.com/track/123456",
                    "duration": "180",
                    "explicit_lyrics": False,
                    "preview": "https://cdns-preview-test.dzcdn.net/stream/test-preview-1.mp3",
                    "artist": {
                        "id": "1001",
                        "name": "Test Artist",
                        "picture_xl": "https://cdn-images.dzcdn.net/images/artist/abc123/1000x1000-000000-80-0-0.jpg",
                        "link": "https://www.deezer.com/artist/1001",
                    },
                    "album": {
                        "id": "2001",
                        "title": "Test Album One",
                        "cover_xl": "https://cdn-images.dzcdn.net/images/cover/abc123def456/1000x1000-000000-80-0-0.jpg",
                    },
                    "type": "track",
                },
                {
                    "id": "123457",
                    "title": "Another Test Track",
                    "link": "https://www.deezer.com/track/123457",
                    "duration": "240",
                    "explicit_lyrics": False,
                    "preview": "https://cdns-preview-test.dzcdn.net/stream/test-preview-2.mp3",
                    "artist": {
                        "id": "1001",
                        "name": "Test Artist",
                        "picture_xl": "https://cdn-images.dzcdn.net/images/artist/abc123/1000x1000-000000-80-0-0.jpg",
                        "link": "https://www.deezer.com/artist/1001",
                    },
                    "album": {
                        "id": "2002",
                        "title": "Test Album Two",
                        "cover_xl": "https://cdn-images.dzcdn.net/images/cover/def789ghi012/1000x1000-000000-80-0-0.jpg",
                    },
                    "type": "track",
                },
            ]
        }


class MockTrackResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "id": 123456,
            "title": "Test Song Title",
            "duration": 180,
            "explicit_lyrics": False,
            "preview": "https://cdns-preview-test.dzcdn.net/stream/test-preview-1.mp3",
            "album": {
                "id": 2001,
                "title": "Test Album One",
                "cover_xl": "https://cdn-images.dzcdn.net/images/cover/abc123def456/1000x1000-000000-80-0-0.jpg",
                "release_date": "2020-01-01",
                "record_type": "album",
                "link": "https://www.deezer.com/album/2001",
            },
            "artist": {
                "id": 1001,
                "name": "Test Artist",
                "picture_xl": "https://cdn-images.dzcdn.net/images/artist/abc123/1000x1000-000000-80-0-0.jpg",
                "link": "https://www.deezer.com/artist/1001",
            },
            "bpm": 120,
            "gain": None,
            "isrc": "TESTISRC",
            "release_date": "2020-01-01",
            "track_position": 1,
            "link": "https://www.deezer.com/track/123456",
        }


class MockAlbumResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "id": 2001,
            "title": "Test Album One",
            "cover_xl": "https://cdn-images.dzcdn.net/images/cover/abc123def456/1000x1000-000000-80-0-0.jpg",
            "duration": 3600,
            "explicit_lyrics": False,
            "genres": {"data": [{"name": "Pop"}]},
            "label": "Test Label",
            "release_date": "2020-01-01",
            "nb_tracks": 2,
            "record_type": "album",
            "upc": "TESTUPC",
            "link": "https://www.deezer.com/album/2001",
            "contributors": [
                {
                    "id": 1001,
                    "name": "Test Artist",
                    "picture_xl": "https://cdn-images.dzcdn.net/images/artist/abc123/1000x1000-000000-80-0-0.jpg",
                    "role": "Main",
                    "link": "https://www.deezer.com/artist/1001",
                }
            ],
            "tracks": {
                "data": [
                    {
                        "id": 123456,
                        "title": "Test Song Title",
                        "duration": 180,
                        "explicit_lyrics": False,
                        "preview": "https://cdns-preview-test.dzcdn.net/stream/test-preview-1.mp3",
                        "artist": {
                            "id": 1001,
                            "name": "Test Artist",
                        },
                        "link": "https://www.deezer.com/track/123456",
                    }
                ]
            },
        }


def test_search_valid(deezer, monkeypatch):
    monkeypatch.setattr(deezer._session, "get", lambda *a, **kw: MockSearchResponse())
    result = deezer.search("Test Artist", "Test Song Title", limit=2)
    assert result is not None
    assert len(result) == 2
    assert result[0].title == "Test Song Title (Extended Version)"
    assert result[1].title == "Another Test Track"


def test_get_track(deezer, monkeypatch):
    monkeypatch.setattr(deezer._session, "get", lambda *a, **kw: MockTrackResponse())
    result = deezer.get_track(123456)
    assert result is not None
    assert result.id == 123456
    assert result.title == "Test Song Title"
    assert result.album.title == "Test Album One"
    assert result.artists[0].name == "Test Artist"


def test_get_album(deezer, monkeypatch):
    monkeypatch.setattr(deezer._session, "get", lambda *a, **kw: MockAlbumResponse())
    result = deezer.get_album(2001)
    assert result is not None
    assert result.id == 2001
    assert result.title == "Test Album One"
    assert result.artists[0].name == "Test Artist"
    assert result.tracks[0].title == "Test Song Title"
