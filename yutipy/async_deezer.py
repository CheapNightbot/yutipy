"""Async Deezer service."""

__all__ = ["AsyncDeezer"]

from typing import Optional

import httpx

from yutipy.async_base_clients import AsyncBaseService
from yutipy.exceptions import InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string


class AsyncDeezer(AsyncBaseService):
    """Async class to interact with the Deezer API."""

    def __init__(self) -> None:
        """Initializes the Deezer service."""
        super().__init__(
            service_name="Deezer",
            service_url="https://www.deezer.com",
            api_url="https://api.deezer.com",
        )

    async def search(
        self,
        artist: str = "",
        song: str = "",
        limit: int = 10,
    ) -> Optional[dict[str, list[Track | Album | Artist]]]:
        """Async search for a song by artist and title.

        Parameters
        ----------
        artist : str, optional
            The name of the artist.
        song : str, optional
            The title of the song.
        limit: int, optional
            The number of items to retrieve from API. ``limit >= 1 and <= 50``. Default is ``10``.

        Returns
        -------
        dict[str, list[Track | Album | Artist]] | None
            A dictionary containing separate lists for tracks, albums, and artists, or None if an error occurs.

        Raises
        ------
        InvalidValueException
            If the artist or song names are invalid or if the limit is out of range.
        """
        if not is_valid_string(artist) and not is_valid_string(song):
            raise InvalidValueException(
                "Artist or song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        if artist and song:
            query = f'?q=artist:"{artist}" track:"{song}"&limit={limit}'
        elif artist:
            query = f'?q=artist:"{artist}"&limit={limit}'
        else:
            query = f'?q=track:"{song}"&limit={limit}'
        query_url = f"{self._api_url}/search/{query}"

        try:
            logger.info(
                f'Searching music info for `artist="{artist}"` and `song="{song}"` (async)'
            )
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = await self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            results = response.json()
        except httpx.RequestError as e:
            logger.warning(f"Unexpected error while searching Deezer: {e}")
            return None

        mapped_results: dict[str, list[Track | Album | Artist]] = {
            "tracks": [],
            "albums": [],
            "artists": [],
        }
        for item in results.get("data", [{}]):
            if item.get("type") == "track":
                track = Track(
                    album=Album(
                        id=item.get("album", {}).get("id"),
                        title=item.get("album", {}).get("title"),
                        cover=item.get("album", {}).get("cover_xl"),
                    ),
                    artists=[
                        Artist(
                            id=item.get("artist", {}).get("id"),
                            name=item.get("artist", {}).get("name"),
                            picture=item.get("artist", {}).get("picture_xl"),
                            url=item.get("artist", {}).get("link"),
                        )
                    ],
                    duration=item.get("duration"),
                    explicit=item.get("explicit_lyrics"),
                    id=item.get("id"),
                    preview_url=item.get("preview"),
                    title=item.get("title"),
                    url=item.get("link"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["tracks"].append(track)
            elif item.get("type") == "album":
                album = Album(
                    artists=[
                        Artist(
                            id=item.get("artist", {}).get("id"),
                            name=item.get("artist", {}).get("name"),
                            picture=item.get("artist", {}).get("picture_xl"),
                            url=item.get("artist", {}).get("link"),
                        )
                    ],
                    cover=item.get("cover_xl"),
                    explicit=item.get("explicit_lyrics"),
                    id=item.get("id"),
                    title=item.get("title"),
                    total_tracks=item.get("nb_tracks"),
                    type=item.get("record_type"),
                    url=item.get("link"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["albums"].append(album)
            elif item.get("type") == "artist":
                artist_obj = Artist(
                    id=item.get("id"),
                    name=item.get("name"),
                    picture=item.get("picture_xl"),
                    url=item.get("link"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["artists"].append(artist_obj)

        return mapped_results if any(mapped_results.values()) else None
