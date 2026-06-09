"""Tests for async YouTube Music service."""

import pytest

from yutipy.async_musicyt import AsyncMusicYT
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def async_musicyt():
    return AsyncMusicYT()


@pytest.mark.asyncio
async def test_search_empty(async_musicyt):
    with pytest.raises(InvalidValueException):
        await async_musicyt.search("", "")


@pytest.mark.asyncio
async def test_search_invalid_limit(async_musicyt):
    with pytest.raises(InvalidValueException):
        await async_musicyt.search("Artist", "Song", limit=0)
    with pytest.raises(InvalidValueException):
        await async_musicyt.search("Artist", "Song", limit=100)


@pytest.mark.asyncio
async def test_async_context_manager(async_musicyt):
    # Note: MusicYT doesn't use async context manager the same way,
    # but this tests basic instantiation
    service = AsyncMusicYT()
    assert service is not None
    assert service.service_name == "YouTube Music"
