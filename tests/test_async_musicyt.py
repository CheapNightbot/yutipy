"""Tests for async YouTube Music service."""

import pytest
from ytmusicapi import exceptions

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


@pytest.mark.asyncio
async def test_get_track_valid(async_musicyt, monkeypatch):
    def mock_get_song_sync(track_id):
        return {
            "videoDetails": {
                "videoId": "testvideo1",
                "title": "Test Track Title",
                "lengthSeconds": "215",
                "author": "Test Artist",
            },
            "microformat": {
                "microformatDataRenderer": {
                    "thumbnail": {
                        "thumbnails": [
                            {"url": "https://music.youtube.com/image/track.jpg"}
                        ]
                    },
                    "publishDate": "2026-06-12",
                    "urlCanonical": "https://music.youtube.com/watch?v=testvideo1",
                    "familySafe": True,
                }
            },
            "streamingData": {
                "adaptiveFormats": [
                    {"url": "https://rr1---sn/track.m4a", "loudnessDb": -1.3}
                ]
            },
        }

    monkeypatch.setattr(async_musicyt, "_get_song_sync", mock_get_song_sync)

    result = await async_musicyt.get_track("testvideo1")

    assert result is not None
    assert result.id == "testvideo1"
    assert result.title == "Test Track Title"
    assert result.duration == 215
    assert result.preview_url == "https://rr1---sn/track.m4a"
    assert result.release_date == "2026-06-12"
    assert result.explicit is False
    assert result.artists[0].name == "Test Artist"
    assert result.album.cover == "https://music.youtube.com/image/track.jpg"
    assert result.url == "https://music.youtube.com/watch?v=testvideo1"


@pytest.mark.asyncio
async def test_get_album_valid(async_musicyt, monkeypatch):
    def mock_get_album_sync(album_id):
        return {
            "artists": [{"id": "artistid1", "name": "Artist One"}],
            "thumbnails": [{"url": "https://music.youtube.com/image/album.jpg"}],
            "duration_seconds": 1234,
            "audioPlaylistId": "playlist1",
            "year": "2026",
            "title": "Test Album",
            "trackCount": 1,
            "tracks": [
                {
                    "artists": [{"id": "artistid1", "name": "Artist One"}],
                    "duration_seconds": 215,
                    "isExplicit": False,
                    "videoId": "testvideo1",
                    "title": "Test Track Title",
                    "trackNumber": 1,
                }
            ],
            "type": "Album",
        }

    monkeypatch.setattr(async_musicyt, "_get_album_sync", mock_get_album_sync)

    result = await async_musicyt.get_album("playlist1")

    assert result is not None
    assert result.id == "playlist1"
    assert result.title == "Test Album"
    assert result.release_date == "2026"
    assert result.total_tracks == 1
    assert result.duration == 1234
    assert result.cover == "https://music.youtube.com/image/album.jpg"
    assert result.url == "https://music.youtube.com/playlist?list=playlist1"
    assert result.artists[0].name == "Artist One"
    assert len(result.tracks) == 1
    assert result.tracks[0].title == "Test Track Title"
    assert result.tracks[0].track_number == 1
    assert result.tracks[0].service_name == "YouTube Music"


@pytest.mark.asyncio
async def test_get_track_handles_server_error(async_musicyt, monkeypatch):
    def raise_error(track_id):
        raise exceptions.YTMusicServerError("Server error")

    monkeypatch.setattr(async_musicyt, "_get_song_sync", raise_error)

    result = await async_musicyt.get_track("bad")

    assert result is None
