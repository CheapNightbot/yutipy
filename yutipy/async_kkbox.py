"""Async KKBox service."""

__all__ = ["AsyncKKBox"]

from typing import Optional

import httpx

from yutipy.async_base_clients import AsyncBaseClient
from yutipy.exceptions import InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string


class AsyncKKBox(AsyncBaseClient):
    """Async class to interact with the KKBOX API."""

    _valid_territories = ("HK", "JP", "MY", "SG", "TW")

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        defer_load: bool = True,
    ) -> None:
        """Initializes the KKBOX async service."""
        super().__init__(
            service_name="KKBOX",
            service_url="https://www.kkbox.com",
            api_url="https://api.kkbox.com/v1.1",
            access_token_url="https://account.kkbox.com/oauth2/token",
            client_id=client_id,
            client_secret=client_secret,
            defer_load=defer_load,
        )

    async def search(
        self,
        artist: str = "",
        song: str = "",
        territory: str = "SG",
        limit: int = 10,
    ) -> Optional[dict[str, list[Track | Album | Artist]]]:
        """Async search for a song by artist and title.

        Parameters
        ----------
        artist : str, optional
            The name of the artist.
        song : str, optional
            The title of the song.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2. Default is ``SG``.
        limit: int, optional
            The number of items to retrieve from API. ``limit >= 1 and <= 50``. Default is ``10``.

        Returns
        -------
        dict[str, list[Track | Album | Artist]] | None
            A dictionary containing separate lists for tracks, albums, and artists, or None if no results found.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        """
        if not is_valid_string(artist) and not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        if territory not in self._valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self._valid_territories} !"
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        if artist and song:
            query = f'"{song}" by "{artist}"'
            type = "track,album"
        elif song:
            query = song
            type = "track,album"
        else:
            query = artist
            type = "artist"

        payload = {
            "q": query,
            "type": type,
            "territory": territory,
            "limit": limit,
        }
        query_url = f"{self._api_url}/search"

        await self._refresh_access_token()
        try:
            logger.info(
                f'Searching KKBOX for `artist="{artist}"` and `song="{song}"` (async)'
            )
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = await self._session.get(
                url=query_url,
                params=payload,
                headers=self._authorization_header(),
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            results = response.json()
        except httpx.RequestError as e:
            logger.warning(f"Unexpected error while searching KKBox: {e}")
            return None

        tracks = results.get("tracks", {}).get("data", [])
        albums = results.get("albums", {}).get("data", [])
        artists = results.get("artists", {}).get("data", [])
        mapped_results: dict[str, list[Track | Album | Artist]] = {
            "tracks": [],
            "albums": [],
            "artists": [],
        }

        for item in tracks:
            album = item.get("album", {})
            track = Track(
                album=Album(
                    cover=album.get("images", [{}])[-1].get("url"),
                    explicit=album.get("explicitness"),
                    title=album.get("name"),
                    id=album.get("id"),
                    release_date=album.get("release_date"),
                    url=album.get("url"),
                ),
                artists=[
                    Artist(
                        id=album.get("artist", {}).get("id"),
                        name=album.get("artist", {}).get("name"),
                        picture=album.get("artist", {})
                        .get("images", [{}])[-1]
                        .get("url"),
                        url=album.get("artist", {}).get("url"),
                    )
                ],
                duration=(item.get("duration", 1000) // 1000),
                explicit=item.get("explicitness"),
                id=item.get("id"),
                isrc=item.get("isrc"),
                title=item.get("name"),
                track_number=item.get("track_number"),
                url=item.get("url"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["tracks"].append(track)

        for item in albums:
            album = Album(
                artists=[
                    Artist(
                        id=item.get("artist", {}).get("id"),
                        name=item.get("artist", {}).get("name"),
                        picture=item.get("artist", {})
                        .get("images", [{}])[-1]
                        .get("url"),
                        url=item.get("artist", {}).get("url"),
                    )
                ],
                cover=item.get("images", [{}])[-1].get("url"),
                explicit=item.get("explicitness"),
                id=item.get("id"),
                release_date=item.get("release_date"),
                title=item.get("name"),
                total_tracks=item.get("track_count"),
                url=item.get("url"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["albums"].append(album)

        for item in artists:
            artist_obj = Artist(
                id=item.get("id"),
                name=item.get("name"),
                picture=item.get("images", [{}])[-1].get("url")
                if item.get("images")
                else None,
                url=item.get("url"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["artists"].append(artist_obj)

        return mapped_results if any(mapped_results.values()) else None
