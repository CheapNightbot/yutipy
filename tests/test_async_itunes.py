"""Tests for async iTunes service."""

import pytest

from tests import BaseResponse
from yutipy.async_itunes import AsyncItunes
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def async_itunes():
    return AsyncItunes()


class MockResponse(BaseResponse):
    @staticmethod
    def json():
        return {"results": []}


@pytest.mark.asyncio
async def test_search_empty(async_itunes):
    with pytest.raises(InvalidValueException):
        await async_itunes.search("", "")


@pytest.mark.asyncio
async def test_search_invalid_limit(async_itunes):
    with pytest.raises(InvalidValueException):
        await async_itunes.search("Artist", "Song", limit=0)
    with pytest.raises(InvalidValueException):
        await async_itunes.search("Artist", "Song", limit=100)


@pytest.mark.asyncio
async def test_async_context_manager(async_itunes):
    async with AsyncItunes() as service:
        assert service is not None
        assert not service.is_session_closed
    assert service.is_session_closed
