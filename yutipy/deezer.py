__all__ = ["Deezer"]

from typing import Optional

import requests

from yutipy.base_clients import BaseService
from yutipy.exceptions import InvalidResponseException, InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string


class Deezer(BaseService):
    """A class to interact with the Deezer API."""

    def __init__(self) -> None:
        """"""
        self.service_url = "https://www.deezer.com"
        super().__init__(
            service_name="Deezer",
            api_url="https://api.deezer.com",
        )

    def search(
        self,
        artist: str,
        song: str,
        limit: int = 10,
    ) -> Optional[list[Track | Album] | None]:
        """
        Searches for a song by artist and title.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        limit: int, optional
            The number of items to retrieve from API. ``limit >=1 and <= 50``. Default is ``10``.

        Returns
        -------
        Optional[list[Track | Album] | None]
            A list of Track or Album objects containing search results, or None if an error occurs.

        Raises
        ------
        InvalidValueException
            If the artist or song names are invalid or if the limit is out of range.
        InvalidResponseException
            If the response from Deezer is invalid.
        """
        if not is_valid_string(artist) or not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        query = f'?q="{song}" artist:"{artist}"&limit={limit}'
        query_url = f"{self._api_url}/search/{query}"

        try:
            logger.info(
                f'Searching music info for `artist="{artist}"` and `song="{song}"`'
            )
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            results = response.json()
        except requests.RequestException as e:
            logger.warning(f"Unexpected error while searching Deezer: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Invalid response received from Deezer: {e}"
            )

        mapped_results: list[Track | Album] = []
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
                mapped_results.append(track)
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
                mapped_results.append(album)

        return mapped_results if mapped_results else None

    def get_track(self, track_id: int) -> Track | None:
        """
        Retrieves track information for a given track ID. Use it if you already have the track ID from Deezer.

        Parameters
        ----------
        track_id : int
            The ID of the track.

        Returns
        -------
        Track | None
            A Track object containing track information or None if not found.

        Raises
        ------
        InvalidResponseException
            If the response from Deezer is invalid.
        """
        query_url = f"{self._api_url}/track/{track_id}"

        try:
            logger.info(f"Fetching track info for track_id: {track_id}")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            track = response.json()
        except requests.RequestException as e:
            logger.warning(f"Unexpected error while fetching track info: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Invalid response received from Deezer: {e}"
            )
        else:
            if track.get("error"):
                logger.warning(
                    f"Deezer API returned an error for track_id {track_id}: {track['error'].get('message')}"
                )
                return None

        return Track(
            album=Album(
                cover=track.get("album", {}).get("cover_xl"),
                id=track.get("album", {}).get("id"),
                release_date=track.get("album", {}).get("release_date"),
                title=track.get("album", {}).get("title"),
                type=track.get("album", {}).get("record_type"),
                url=track.get("album", {}).get("link"),
            ),
            artists=[
                Artist(
                    id=track.get("artist", {}).get("id"),
                    name=track.get("artist", {}).get("name"),
                    picture=track.get("artist", {}).get("picture_xl"),
                    url=track.get("artist", {}).get("link"),
                )
            ],
            bpm=None if track.get("bpm") == 0 else track.get("bpm"),
            duration=track.get("duration"),
            explicit=track.get("explicit_lyrics"),
            gain=track.get("gain"),
            id=track.get("id"),
            isrc=track.get("isrc"),
            preview_url=track.get("preview"),
            release_date=track.get("release_date"),
            title=track.get("title"),
            track_number=track.get("track_position"),
            url=track.get("link"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_album(self, album_id: int) -> Album | None:
        """
        Retrieves album information for a given album ID. Use it if you already have the album ID from Deezer.

        Parameters
        ----------
        album_id : int
            The ID of the album.

        Returns
        -------
        Album | None
            An Album object containing album information or None if not found.

        Raises
        ------
        InvalidResponseException
            If the response from Deezer is invalid.
        """
        query_url = f"{self._api_url}/album/{album_id}"
        try:
            logger.info(f"Fetching album info for album_id: {album_id}")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            album = response.json()
        except requests.RequestException as e:
            logger.warning(f"Unexpected error while fetching album info: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Invalid response received from Deezer: {e}"
            )
        else:
            if album.get("error"):
                logger.warning(
                    f"Deezer API returned an error for album_id {album_id}: {album['error'].get('message')}"
                )
                return None

        return Album(
            artists=[
                Artist(
                    id=artist.get("id"),
                    name=artist.get("name"),
                    picture=artist.get("picture_xl"),
                    role=artist.get("role"),
                    url=artist.get("link"),
                )
                for artist in album.get("contributors", [{}])
            ],
            cover=album.get("cover_xl"),
            duration=album.get("duration"),
            explicit=album.get("explicit_lyrics"),
            genres=[
                genre.get("name") for genre in album.get("genres", {}).get("data", [{}])
            ],
            id=album.get("id"),
            label=album.get("label"),
            release_date=album.get("release_date"),
            title=album.get("title"),
            total_tracks=album.get("nb_tracks"),
            tracks=[
                Track(
                    artists=[
                        Artist(
                            id=track.get("artist", {}).get("id"),
                            name=track.get("artist", {}).get("name"),
                        )
                    ],
                    duration=track.get("duration"),
                    explicit=track.get("explicit_lyrics"),
                    id=track.get("id"),
                    preview_url=track.get("preview"),
                    title=track.get("title"),
                    track_number=idx + 1,
                    url=track.get("link"),
                )
                for idx, track in enumerate(album.get("tracks", {}).get("data", [{}]))
            ],
            type=album.get("record_type"),
            upc=album.get("upc"),
            url=album.get("link"),
            service_name=self.service_name,
            service_url=self.service_url,
        )
