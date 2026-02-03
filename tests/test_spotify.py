import pytest

from tests import BaseResponse
from yutipy.exceptions import InvalidValueException
from yutipy.models import Album, Artist, Track
from yutipy.spotify import Spotify, SpotifyAuth


@pytest.fixture
def spotify():
    return Spotify(client_id="test_id", client_secret="test_secret", defer_load=True)


@pytest.fixture
def spotify_auth():
    return SpotifyAuth(
        client_id="test_id",
        client_secret="test_secret",
        redirect_uri="http://localhost/callback",
        scopes=["user-read-email"],
        defer_load=True,
    )


class MockSearchResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "tracks": {
                "items": [
                    {
                        "album": {
                            "album_type": "album",
                            "id": "album1",
                            "images": [
                                {"url": "https://open.spotify.com/image/album1.jpg"}
                            ],
                            "name": "Test Album",
                            "release_date": "2022-01-01",
                            "total_tracks": 10,
                            "type": "album",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/album/album1"
                            },
                        },
                        "artists": [
                            {
                                "id": "artist1",
                                "name": "Artist X",
                                "external_urls": {
                                    "spotify": "https://open.spotify.com/artist/artist1"
                                },
                            }
                        ],
                        "duration_ms": 123000,
                        "explicit": False,
                        "id": "track1",
                        "external_ids": {"isrc": "ISRC123"},
                        "name": "Test Track",
                        "track_number": 1,
                        "external_urls": {
                            "spotify": "https://open.spotify.com/track/track1"
                        },
                    }
                ]
            },
            "albums": {
                "items": [
                    {
                        "album_type": "album",
                        "id": "album1",
                        "images": [
                            {"url": "https://open.spotify.com/image/album1.jpg"}
                        ],
                        "name": "Test Album",
                        "release_date": "2022-01-01",
                        "total_tracks": 10,
                        "type": "album",
                        "external_urls": {
                            "spotify": "https://open.spotify.com/album/album1"
                        },
                        "artists": [
                            {
                                "id": "artist1",
                                "name": "Artist X",
                                "external_urls": {
                                    "spotify": "https://open.spotify.com/artist/artist1"
                                },
                            }
                        ],
                    }
                ]
            },
        }


class MockTrackResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "album": {
                "album_type": "album",
                "id": "album1",
                "images": [{"url": "https://open.spotify.com/image/album1.jpg"}],
                "name": "Test Album",
                "release_date": "2022-01-01",
                "total_tracks": 10,
                "type": "album",
                "external_urls": {"spotify": "https://open.spotify.com/album/album1"},
                "artist": [
                    {
                        "id": "artist1",
                        "name": "Artist X",
                        "external_urls": {
                            "spotify": "https://open.spotify.com/artist/artist1"
                        },
                    }
                ],
            },
            "artists": [
                {
                    "id": "artist1",
                    "name": "Artist X",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/artist1"
                    },
                }
            ],
            "duration_ms": 123000,
            "explicit": False,
            "id": "track1",
            "external_ids": {"isrc": "ISRC123"},
            "name": "Test Track",
            "track_number": 1,
            "external_urls": {"spotify": "https://open.spotify.com/track/track1"},
        }


class MockAlbumResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "album_type": "album",
            "id": "album1",
            "images": [{"url": "https://open.spotify.com/image/album1.jpg"}],
            "name": "Test Album",
            "release_date": "2022-01-01",
            "total_tracks": 10,
            "type": "album",
            "external_urls": {"spotify": "https://open.spotify.com/album/album1"},
            "artist": [
                {
                    "id": "artist1",
                    "name": "Artist X",
                    "external_urls": {
                        "spotify": "https://open.spotify.com/artist/artist1"
                    },
                }
            ],
            "tracks": [
                {
                    "artists": [
                        {
                            "id": "artist1",
                            "name": "Artist X",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/artist1"
                            },
                        }
                    ],
                    "duration_ms": 123000,
                    "explicit": False,
                    "id": "track1",
                    "name": "Test Track",
                    "track_number": 1,
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/track1"
                    },
                }
            ],
            "label": "Test Label",
            "external_ids": {"upc": "UPC123"},
        }


class MockArtistResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "id": "artist1",
            "name": "Artist X",
            "genres": ["pop"],
            "images": [{"url": "https://open.spotify.com/image/artist1.jpg"}],
            "external_urls": {"spotify": "https://open.spotify.com/artist/artist1"},
        }


class MockUserProfileResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "display_name": "Test User",
            "images": [{"url": "https://open.spotify.com/image/user.jpg"}],
            "external_urls": {"spotify": "https://open.spotify.com/user/testuser"},
        }


class MockCurrentlyPlayingResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "item": {
                "album": {
                    "album_type": "compilation",
                    "total_tracks": 9,
                    "id": "album123",
                    "images": [
                        {
                            "url": "https://open.spotify.com/image/album123.jpg",
                            "height": 300,
                            "width": 300,
                        }
                    ],
                    "name": "Test Compilation Album",
                    "release_date": "1981-12",
                    "release_date_precision": "year",
                    "type": "album",
                    "uri": "spotify:album:album123",
                    "artists": [
                        {
                            "id": "artist123",
                            "name": "Artist Y",
                            "type": "artist",
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/artist123"
                            },
                        }
                    ],
                    "external_urls": {
                        "spotify": "https://open.spotify.com/album/album123"
                    },
                },
                "artists": [
                    {
                        "id": "artist123",
                        "name": "Artist Y",
                        "type": "artist",
                        "external_urls": {
                            "spotify": "https://open.spotify.com/artist/artist123"
                        },
                    }
                ],
                "duration_ms": 234000,
                "explicit": False,
                "external_ids": {"isrc": "ISRC123", "ean": "EAN123", "upc": "UPC123"},
                "id": "track123",
                "name": "Test Compilation Track",
                "preview_url": "https://open.spotify.com/preview/track123.mp3",
                "track_number": 1,
                "type": "track",
                "uri": "spotify:track:track123",
                "external_urls": {"spotify": "https://open.spotify.com/track/track123"},
            }
        }


@pytest.fixture
def mock_search_response(spotify, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockSearchResponse()

    monkeypatch.setattr(spotify._session, "get", mock_get)


@pytest.fixture
def mock_track_response(spotify, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockTrackResponse()

    monkeypatch.setattr(spotify._session, "get", mock_get)


@pytest.fixture
def mock_album_response(spotify, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockAlbumResponse()

    monkeypatch.setattr(spotify._session, "get", mock_get)


@pytest.fixture
def mock_artist_response(spotify, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockArtistResponse()

    monkeypatch.setattr(spotify._session, "get", mock_get)


@pytest.fixture
def mock_user_profile_response(spotify_auth, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockUserProfileResponse()

    monkeypatch.setattr(spotify_auth._session, "get", mock_get)


@pytest.fixture
def mock_currently_playing_response(spotify_auth, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockCurrentlyPlayingResponse()

    monkeypatch.setattr(spotify_auth._session, "get", mock_get)


def test_search_valid(spotify, mock_search_response):
    result = spotify.search("Artist X", "Test Track")
    assert result is not None
    assert any(isinstance(x, Track) for x in result)
    assert any(isinstance(x, Album) for x in result)
    assert result[0].title == "Test Track"
    assert result[1].title == "Test Album"


def test_search_empty_artist(spotify, mock_search_response):
    result = spotify.search(song="Test Track")
    assert result is not None


def test_search_empty_song(spotify, mock_search_response):
    result = spotify.search(artist="Artist X")
    assert result is not None


def test_search_empty(spotify, mock_search_response):
    with pytest.raises(InvalidValueException):
        spotify.search("", "")


def test_get_track(spotify, mock_track_response):
    result = spotify.get_track("track1")
    assert result is not None
    assert isinstance(result, Track)
    assert result.title == "Test Track"
    assert result.album.title == "Test Album"
    assert result.artists[0].name == "Artist X"


def test_get_album(spotify, mock_album_response):
    result = spotify.get_album("album1")
    assert result is not None
    assert isinstance(result, Album)
    assert result.title == "Test Album"
    assert result.artists[0].name == "Artist X"
    assert result.tracks[0].title == "Test Track"


def test_get_artist(spotify, mock_artist_response):
    result = spotify.get_artist("artist1")
    assert result is not None
    assert isinstance(result, Artist)
    assert result.name == "Artist X"
    assert result.url == "https://open.spotify.com/artist/artist1"


def test_auth_get_user_profile(spotify_auth, mock_user_profile_response):
    result = spotify_auth.get_user_profile()
    assert result is not None
    assert result["display_name"] == "Test User"
    assert result["images"][0]["url"] == "https://open.spotify.com/image/user.jpg"
    assert result["url"] == "https://open.spotify.com/user/testuser"


def test_auth_get_currently_playing(spotify_auth, mock_currently_playing_response):
    result = spotify_auth.get_currently_playing()
    assert result is not None
    assert result.title == "Test Compilation Track"
    assert result.album.title == "Test Compilation Album"
    assert result.album.cover == "https://open.spotify.com/image/album123.jpg"
    assert result.artists[0].name == "Artist Y"
    assert result.album.artists[0].name == "Artist Y"
    assert result.url == "https://open.spotify.com/track/track123"
    assert result.album.url == "https://open.spotify.com/album/album123"
    assert result.preview_url == "https://open.spotify.com/preview/track123.mp3"
    assert result.isrc == "ISRC123"
    assert result.duration == 234


def test_close_session(spotify):
    spotify.close_session()
    assert spotify.is_session_closed


def test_spotify_auth_close_session(spotify_auth):
    spotify_auth.close_session()
    assert spotify_auth.is_session_closed
