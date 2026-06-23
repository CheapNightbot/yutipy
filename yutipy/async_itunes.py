"""Async iTunes service."""

__all__ = ["AsyncItunes"]

from datetime import datetime
from typing import Optional

import httpx

from yutipy.async_base_clients import AsyncBaseService
from yutipy.exceptions import InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import guess_album_type, is_valid_string


class AsyncItunes(AsyncBaseService):
    """Async class to interact with the iTunes API."""

    def __init__(
        self,
        language: str = "en",
        location: str = "US",
    ) -> None:
        """Initializes the iTunes async service.

        Parameters
        ----------
        language: str, optional
            The language, English or Japanese, you want to use when returning search results. The default is `en` (English).
        location: str, optional
            The two-letter country code for the store you want to search. The default is `US`.
        """
        self.language = f"{language.lower()}_{location.lower()}"
        self.location = location.lower()

        super().__init__(
            service_name="iTunes",
            service_url="https://music.apple.com",
            api_url="https://itunes.apple.com",
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
            A dictionary containing separate lists for tracks, albums, and artists, or None if no results are found.

        Raises
        ------
        InvalidValueException
            If the artist or song name is invalid, or if the limit is out of range.
        """
        if not is_valid_string(artist) and not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        if artist and song:
            term = f"{song} by {artist}"
            entity = "song,album"
        elif song:
            term = song
            entity = "song,album"
        else:
            term = artist
            entity = "musicArtist"

        payload = {
            "term": term,
            "entity": entity,
            "media": "music",
            "limit": limit,
            "country": self.location,
            "lang": self.language,
        }
        query_url = f"{self._api_url}/search"

        try:
            logger.info(
                f'Searching iTunes for `artist="{artist}"` and `song="{song}"` (async)'
            )
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = await self._session.get(
                url=query_url,
                params=payload,
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            result = response.json()
        except httpx.RequestError as e:
            logger.warning(f"Unexpected error while searching iTunes: {e}")
            return None

        mapped_results: dict[str, list[Track | Album | Artist]] = {
            "tracks": [],
            "albums": [],
            "artists": [],
        }
        for item in result.get("results", []):
            kind = item.get("kind")
            wrapper_type = item.get("wrapperType")

            if kind == "song" and wrapper_type == "track":
                track = Track(
                    album=Album(
                        cover=item.get("artworkUrl100"),
                        explicit=item.get("collectionExplicitness") == "explicit",
                        id=item.get("collectionId"),
                        title=item.get("collectionName"),
                        total_tracks=item.get("trackCount"),
                        type=guess_album_type(item.get("trackCount", 0)),
                        url=item.get("collectionViewUrl"),
                    ),
                    artists=[
                        Artist(
                            id=item.get("artistId"),
                            name=item.get("artistName"),
                            url=item.get("artistViewUrl"),
                        )
                    ],
                    duration=(item.get("trackTimeMillis", 1000) // 1000),
                    explicit=item.get("trackExplicitness") == "explicit",
                    genre=item.get("primaryGenreName"),
                    id=item.get("trackId"),
                    preview_url=item.get("previewUrl"),
                    release_date=self._format_release_date(item.get("releaseDate", "")),
                    title=item.get("trackName"),
                    track_number=item.get("trackNumber"),
                    url=item.get("trackViewUrl"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["tracks"].append(track)

            elif wrapper_type == "collection":
                album = Album(
                    artists=[
                        Artist(
                            id=item.get("artistId"),
                            name=item.get("artistName"),
                            url=item.get("artistViewUrl"),
                        )
                    ],
                    cover=item.get("artworkUrl100"),
                    explicit=item.get("collectionExplicitness") == "explicit",
                    genres=[item.get("primaryGenreName")],
                    id=item.get("collectionId"),
                    release_date=self._format_release_date(item.get("releaseDate", "")),
                    title=item.get("collectionName"),
                    total_tracks=item.get("trackCount"),
                    type=guess_album_type(item.get("trackCount", 0)),
                    url=item.get("collectionViewUrl"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results["albums"].append(album)

        return mapped_results if any(mapped_results.values()) else None

    @staticmethod
    def _format_release_date(release_date: str) -> str:
        """Format the release date from iTunes format."""
        try:
            return datetime.fromisoformat(release_date.replace("Z", "+00:00")).strftime(
                "%Y-%m-%d"
            )
        except (ValueError, AttributeError):
            return release_date
