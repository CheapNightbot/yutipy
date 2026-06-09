"""Tests for async KKBox service."""

import pytest

from yutipy.async_kkbox import AsyncKKBox
from yutipy.exceptions import InvalidValueException


@pytest.fixture
def async_kkbox():
    def mock_get_access_token(*args, **kwargs):
        return {
            "access_token": "test_access_token",
            "expires_in": 3600,
            "requested_at": 1234567890,
        }

    kkbox_instance = AsyncKKBox(
        client_id="test_client_id",
        client_secret="test_client_secret",
        defer_load=True,
    )
    kkbox_instance._get_access_token = mock_get_access_token
    return kkbox_instance


@pytest.mark.asyncio
async def test_search_empty(async_kkbox):
    with pytest.raises(InvalidValueException):
        await async_kkbox.search("", "")


@pytest.mark.asyncio
async def test_invalid_territory(async_kkbox):
    with pytest.raises(InvalidValueException):
        await async_kkbox.search("Artist", "Song", territory="US")


@pytest.mark.asyncio
async def test_async_context_manager(async_kkbox):
    async with AsyncKKBox(client_id="test", client_secret="test", defer_load=True) as service:
        assert service is not None
        assert not service.is_session_closed
    assert service.is_session_closed
