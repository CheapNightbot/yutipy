"""Tests for async Deezer service."""

import pytest

from tests import BaseResponse
from yutipy.async_deezer import AsyncDeezer
from yutipy.exceptions import InvalidValueException
from yutipy.models import Album, Artist, Track


@pytest.fixture
def async_deezer():
    return AsyncDeezer()


class MockSearchResponse(BaseResponse):
    @staticmethod
    def json():
        return {
            "data": [
                {
                    "id": "123456",
                    "title": "Test Song",
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
                        "title": "Test Album",
                        "cover_xl": "https://cdn-images.dzcdn.net/images/cover/abc123def456/1000x1000-000000-80-0-0.jpg",
                    },
                    "type": "track",
                },
                {
                    "id": "1001",
                    "name": "Test Artist",
                    "picture_xl": "https://cdn-images.dzcdn.net/images/artist/abc123/1000x1000-000000-80-0-0.jpg",
                    "link": "https://www.deezer.com/artist/1001",
                    "type": "artist",
                },
            ]
        }


@pytest.mark.asyncio
async def test_search_valid(async_deezer, monkeypatch):
    class MockSession:
        async def get(self, *a, **kw):
            return MockSearchResponse()

    monkeypatch.setattr(async_deezer, "_session", MockSession())
    result = await async_deezer.search("Test Artist", "Test Song", limit=2)
    assert result is not None
    assert len(result["tracks"]) == 1
    assert len(result["artists"]) == 1
    assert isinstance(result["tracks"][0], Track)
    assert isinstance(result["artists"][0], Artist)


@pytest.mark.asyncio
async def test_search_empty(async_deezer):
    with pytest.raises(InvalidValueException):
        await async_deezer.search("", "")


@pytest.mark.asyncio
async def test_async_context_manager(async_deezer):
    async with AsyncDeezer() as service:
        assert service is not None
        assert not service.is_session_closed
    assert service.is_session_closed
