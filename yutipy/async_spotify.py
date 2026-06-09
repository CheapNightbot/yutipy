"""Async Spotify service."""

__all__ = ["AsyncSpotify"]

from typing import Optional

import httpx

from yutipy.async_base_clients import AsyncBaseClient
from yutipy.exceptions import InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string


class AsyncSpotify(AsyncBaseClient):
    """Async class to interact with the Spotify Web API."""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        defer_load: bool = True,
    ) -> None:
        """Initializes the Spotify async service."""
        super().__init__(
            service_name="Spotify",
            service_url="https://open.spotify.com",
            api_url="https://api.spotify.com/v1",
            access_token_url="https://accounts.spotify.com/api/token",
            client_id=client_id,
            client_secret=client_secret,
            defer_load=defer_load,
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
            If the input values are invalid.
        """
        if not is_valid_string(artist) and not is_valid_string(song):
            raise InvalidValueException(
                "Artist or song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        if artist and song:
            query_type = "track,artist,album"
            query = f'q="{song}" artist:"{artist}"&type={query_type}&limit={limit}'
        elif artist:
            query_type = "artist"
            query = f'q="{artist}"&type={query_type}&limit={limit}'
        else:
            query_type = "track,album"
            query = f'q="{song}"&type={query_type}&limit={limit}'

        query_url = f"{self._api_url}/search?{query}"

        await self._refresh_access_token()
        try:
            logger.info(
                f'Searching Spotify for `artist="{artist}"` and `song="{song}"` (async)'
            )
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = await self._session.get(
                query_url,
                headers=self._authorization_header(),
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            results = response.json()
        except httpx.RequestError as e:
            logger.warning(f"Unexpected error while searching Spotify: {e}")
            return None

        mapped_results: dict[str, list[Track | Album | Artist]] = {
            "tracks": [],
            "albums": [],
            "artists": [],
        }

        for item in results.get("tracks", {}).get("items", []):
            track = Track(
                album=Album(
                    cover=item.get("album", {}).get("images", [{}])[0].get("url"),
                    id=item.get("album", {}).get("id"),
                    release_date=item.get("album", {}).get("release_date"),
                    title=item.get("album", {}).get("name"),
                    total_tracks=item.get("album", {}).get("total_tracks"),
                    url=item.get("album", {}).get("external_urls", {}).get("spotify"),
                ),
                artists=[
                    Artist(
                        id=artist_item.get("id"),
                        name=artist_item.get("name"),
                        url=artist_item.get("external_urls", {}).get("spotify"),
                    )
                    for artist_item in item.get("artists", [])
                ],
                duration=(item.get("duration_ms", 0) // 1000),
                explicit=item.get("explicit"),
                id=item.get("id"),
                preview_url=item.get("preview_url"),
                title=item.get("name"),
                track_number=item.get("track_number"),
                url=item.get("external_urls", {}).get("spotify"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["tracks"].append(track)

        for item in results.get("albums", {}).get("items", []):
            album = Album(
                artists=[
                    Artist(
                        id=artist_item.get("id"),
                        name=artist_item.get("name"),
                        url=artist_item.get("external_urls", {}).get("spotify"),
                    )
                    for artist_item in item.get("artists", [])
                ],
                cover=item.get("images", [{}])[0].get("url"),
                explicit=item.get("explicit"),
                id=item.get("id"),
                release_date=item.get("release_date"),
                title=item.get("name"),
                total_tracks=item.get("total_tracks"),
                url=item.get("external_urls", {}).get("spotify"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["albums"].append(album)

        for item in results.get("artists", {}).get("items", []):
            artist_obj = Artist(
                genres=item.get("genres", []),
                id=item.get("id"),
                name=item.get("name"),
                picture=item.get("images", [{}])[0].get("url") if item.get("images") else None,
                url=item.get("external_urls", {}).get("spotify"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["artists"].append(artist_obj)

        return mapped_results if any(mapped_results.values()) else None
