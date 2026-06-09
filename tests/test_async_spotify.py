"""Tests for async Spotify service."""

import pytest

from tests import BaseResponse
from yutipy.async_spotify import AsyncSpotify
from yutipy.exceptions import InvalidValueException
from yutipy.models import Track, Album, Artist


@pytest.fixture
def async_spotify():
    def mock_get_access_token(*args, **kwargs):
        return {
            "access_token": "test_access_token",
            "expires_in": 3600,
            "requested_at": 1234567890,
        }

    spotify_instance = AsyncSpotify(
        client_id="test_id",
        client_secret="test_secret",
        defer_load=True,
    )
    spotify_instance._get_access_token = mock_get_access_token
    return spotify_instance


class MockSearchResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "tracks": {
                "items": [
                    {
                        "id": "track1",
                        "name": "Test Track",
                        "duration_ms": 123000,
                        "explicit": False,
                        "preview_url": "https://p.scdn.co/preview.mp3",
                        "album": {
                            "id": "album1",
                            "name": "Test Album",
                            "release_date": "2022-01-01",
                            "total_tracks": 10,
                            "images": [{"url": "https://open.spotify.com/image/album1.jpg"}],
                            "external_urls": {"spotify": "https://open.spotify.com/album/album1"},
                        },
                        "artists": [
                            {
                                "id": "artist1",
                                "name": "Artist X",
                                "external_urls": {"spotify": "https://open.spotify.com/artist/artist1"},
                            }
                        ],
                        "external_urls": {"spotify": "https://open.spotify.com/track/track1"},
                        "track_number": 1,
                    }
                ]
            },
            "albums": {"items": []},
            "artists": {
                "items": [
                    {
                        "id": "artist1",
                        "name": "Artist X",
                        "genres": ["pop"],
                        "images": [{"url": "https://open.spotify.com/image/artist1.jpg"}],
                        "external_urls": {"spotify": "https://open.spotify.com/artist/artist1"},
                    }
                ]
            },
        }


@pytest.mark.asyncio
async def test_search_empty(async_spotify):
    with pytest.raises(InvalidValueException):
        await async_spotify.search("", "")


@pytest.mark.asyncio
async def test_async_context_manager(async_spotify):
    async with AsyncSpotify(client_id="test", client_secret="test", defer_load=True) as service:
        assert service is not None
        assert not service.is_session_closed
    assert service.is_session_closed
