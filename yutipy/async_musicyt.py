"""Async YouTube Music service."""

__all__ = ["AsyncMusicYT"]

import asyncio
from typing import Optional

from ytmusicapi import YTMusic, exceptions

from yutipy.async_base_clients import AsyncBaseService
from yutipy.exceptions import InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string


class AsyncMusicYT(AsyncBaseService):
    """Async class to interact with the YouTube Music API.

    Note: YouTube Music API (ytmusicapi) is synchronous. This class wraps
    it for async compatibility by running calls in a thread pool.
    """

    def __init__(self) -> None:
        """Initializes the YouTube Music async service."""
        super().__init__(
            service_name="YouTube Music",
            service_url="https://music.youtube.com",
            api_url="",
        )
        self.ytmusic = YTMusic()

    async def search(
        self,
        artist: str = "",
        song: str = "",
        limit: int = 10,
    ) -> Optional[dict[str, list[Track | Album | Artist]]]:
        """Async search for a song by artist and title.

        Parameters
        ----------
        artist: str, optional
            The name of the artist.
        song: str, optional
            The title of the song.
        limit: int, optional
            The number of the items to retrieve from API. ``limit >= 1 and <= 50``. Default is ``10``.

        Returns
        -------
        dict[str, list[Track | Album | Artist]] | None
            A dictionary containing separate lists for tracks, albums, and artists, or None if no results are found.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        """
        if not is_valid_string(artist) and not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )
        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        query = f"{artist} - {song}"
        if artist and not song:
            search_filter = "artists"
        else:
            search_filter = None

        try:
            logger.info(
                f"Searching YouTube Music for `artist='{artist}'` and `song='{song}'` (async)"
            )
            # Run the sync ytmusicapi call in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                query,
                limit,
                search_filter,
            )
        except Exception as e:
            logger.warning(f"Something went wrong while searching YTMusic: {e}")
            return None

        mapped_results: dict[str, list[Track | Album | Artist]] = {
            "tracks": [],
            "albums": [],
            "artists": [],
        }
        for result in results:
            if not self._is_relevant_result(result):
                continue
            if result.get("resultType") in ["song", "video"]:
                track = Track(
                    album=Album(
                        cover=result.get("thumbnails", [{}])[-1].get("url"),
                        title=result.get("album"),
                    ),
                    artists=[
                        Artist(
                            id=artist_item.get("id"),
                            name=artist_item.get("name"),
                        )
                        for artist_item in result.get("artists", [{}])
                    ],
                    duration=result.get("duration_seconds"),
                    explicit=result.get("isExplicit"),
                    id=result.get("videoId"),
                    title=result.get("title"),
                    url=f"{self.service_url}/watch?v={result.get('videoId')}",
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["tracks"].append(track)
            elif result.get("resultType") == "album":
                album = Album(
                    artists=[
                        Artist(
                            id=artist_item.get("id"),
                            name=artist_item.get("name"),
                        )
                        for artist_item in result.get("artists", [{}])
                    ],
                    cover=result.get("thumbnails", [{}])[-1].get("url"),
                    explicit=result.get("isExplicit"),
                    id=result.get("browseId"),
                    title=result.get("title"),
                    type=(result.get("type", "") or "").lower(),
                    url=f"{self.service_url}/browse/{result.get('browseId')}",
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["albums"].append(album)

            elif result.get("resultType") == "artist":
                artist_obj = Artist(
                    id=result.get("browseId"),
                    name=result.get("artist"),
                    url=f"{self.service_url}/artist/{result.get('browseId')}",
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["artists"].append(artist_obj)

        return mapped_results if any(mapped_results.values()) else None

    async def get_track(self, track_id: str) -> Optional[Track]:
        """Async get a track by its ID (i.e. Video ID from YouTube Music).

        Parameters
        ----------
        track_id : str
            The ID of the track.

        Returns
        -------
        Track | None
            The track object if found, else None.
        """
        try:
            logger.info(f"Getting track with ID '{track_id}' from YouTube Music (async)")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_song_sync, track_id)
        except exceptions.YTMusicServerError as e:
            logger.warning(f"Something went wrong while getting track from YTMusic: {e}")
            return None

        if not result:
            return None

        details = result.get("videoDetails", {})
        data = result.get("microformat", {}).get("microformatDataRenderer", {})
        streaming = result.get("streamingData", {}).get("adaptiveFormats", [{}])[0]

        track = Track(
            album=Album(
                cover=data.get("thumbnail", {}).get("thumbnails", [{}])[-1].get("url"),
            ),
            artists=[Artist(name=details.get("author"))],
            duration=int(
                details.get("lengthSeconds", 0)
                or data.get("videoDetails", {}).get("durationSeconds", 0)
            ),
            explicit=data.get("familySafe", True) is False,
            gain=streaming.get("loudnessDb"),
            id=details.get("videoId"),
            preview_url=streaming.get("url"),
            release_date=data.get("publishDate"),
            title=details.get("title"),
            url=data.get("urlCanonical")
            or f"{self.service_url}/watch?v={details.get('videoId')}",
            service_name=self.service_name,
            service_url=self.service_url,
        )
        return track

    async def get_album(self, album_id: str) -> Optional[Album]:
        """Async get an album by its ID (i.e. Browse ID or Playlist ID from YouTube Music).

        Parameters
        ----------
        album_id : str
            The ID of the album.

        Returns
        -------
        Album | None
            The album object if found, else None.
        """
        try:
            logger.info(f"Getting album with ID '{album_id}' from YouTube Music (async)")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_album_sync, album_id)
        except exceptions.YTMusicServerError as e:
            logger.warning(f"Something went wrong while getting album from YTMusic: {e}")
            return None

        if not result:
            return None

        album = Album(
            artists=[
                Artist(
                    id=artist_item.get("id"),
                    name=artist_item.get("name"),
                )
                for artist_item in result.get("artists", [{}])
            ],
            cover=result.get("thumbnails", [{}])[-1].get("url"),
            duration=int(result.get("duration_seconds", 0)),
            id=result.get("audioPlaylistId"),
            release_date=result.get("year"),
            title=result.get("title"),
            total_tracks=result.get("trackCount"),
            tracks=[
                Track(
                    artists=(
                        [
                            Artist(id=artist_item.get("id"), name=artist_item.get("name"))
                            for artist_item in track.get("artists", [{}])
                        ]
                        if track.get("artists")
                        else None
                    ),
                    duration=int(track.get("duration_seconds", 0)),
                    explicit=track.get("isExplicit"),
                    id=track.get("videoId"),
                    title=track.get("title"),
                    track_number=track.get("trackNumber"),
                    url=f"{self.service_url}/watch?v={track.get('videoId')}",
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                for track in result.get("tracks", [])
            ],
            type=(result.get("type", "") or "").lower(),
            url=f"{self.service_url}/playlist?list={result.get('audioPlaylistId')}",
            service_name=self.service_name,
            service_url=self.service_url,
        )
        return album

    def _get_song_sync(self, track_id: str) -> dict:
        """Synchronous song fetch wrapper for use in async context."""
        return self.ytmusic.get_song(track_id)

    def _get_album_sync(self, album_id: str) -> dict:
        """Synchronous album fetch wrapper for use in async context."""
        return self.ytmusic.get_album(album_id)

    def _search_sync(self, query: str, limit: int, search_filter: Optional[str]) -> list:
        """Synchronous search wrapper for use in async context."""
        if search_filter:
            return self.ytmusic.search(query=query, limit=limit, filter=search_filter)
        else:
            return self.ytmusic.search(query=query, limit=limit)

    def _is_relevant_result(self, result: dict) -> bool:
        """Filters out categories and irrelevant results."""
        return result.get("category") != "Top result" or self._skip_categories(result)

    def _skip_categories(self, result: dict) -> bool:
        """Skips certain categories."""
        return result.get("resultType") not in [
            "song",
            "video",
            "album",
            "artist",
            "playlist",
        ]
