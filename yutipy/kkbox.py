__all__ = ["KKBox"]

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

from yutipy.base_clients import BaseClient
from yutipy.exceptions import AuthenticationException, InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import is_valid_string

load_dotenv()

KKBOX_CLIENT_ID = os.getenv("KKBOX_CLIENT_ID")
KKBOX_CLIENT_SECRET = os.getenv("KKBOX_CLIENT_SECRET")


class KKBox(BaseClient):
    """
    A class to interact with KKBOX Open API.

    This class reads the ``KKBOX_CLIENT_ID`` and ``KKBOX_CLIENT_SECRET`` from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide these values when creating an object.
    """

    def __init__(
        self,
        client_id: Optional[str] = KKBOX_CLIENT_ID,
        client_secret: Optional[str] = KKBOX_CLIENT_SECRET,
        defer_load: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        client_id : str, optional
            The Client ID for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_ID`` from .env file.
        client_secret : str, optional
            The Client secret for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_SECRET`` from .env file.
        defer_load : bool, optional
            Whether to defer loading the access token during initialization. Default is ``False``.

        Raises
        ------
        AuthenticationException
            If the Client ID or Client Secret is not provided.
        """
        if not client_id:
            raise AuthenticationException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not client_secret:
            raise AuthenticationException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        super().__init__(
            service_name="KKBox",
            service_url="https://www.kkbox.com",
            api_url="https://api.kkbox.com/v1.1",
            access_token_url="https://account.kkbox.com/oauth2/token",
            client_id=client_id,
            client_secret=client_secret,
            defer_load=defer_load,
        )

        self._valid_territories = ["HK", "JP", "MY", "SG", "TW"]

    def search(
        self,
        artist: str = "",
        song: str = "",
        territory: str = "SG",
        limit: int = 10,
    ) -> Optional[dict[str, list[Track | Album | Artist]]]:
        """
        Searches for a song by artist and title.

        Parameters
        ----------
        artist : str, optional
            The name of the artist.
        song : str, optional
            The title of the song.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2. Default is ``SG``.
            Allowed values: ``HK``, ``JP``, ``MY``, ``SG``, ``TW``.
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

        self._refresh_access_token()
        try:
            logger.info(f"Searching KKBOX for `artist='{artist}'` and `song='{song}'`")
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = self._session.get(
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
                url=item.get("url"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["albums"].append(album)

        for item in artists:
            artist_ = Artist(
                id=item.get("id"),
                name=item.get("name"),
                url=item.get("url"),
                picture=item.get("images", [{}])[-1].get("url"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results["artists"].append(artist_)

        return mapped_results if any(mapped_results.values()) else None

    def get_track(
        self,
        track_id: str,
        territory: str = "SG",
    ) -> Optional[Track]:
        """
        Retrieves track information for a given track ID. Use it if you already have the track ID from KKBox.

        Parameters
        ----------
        track_id : int
            The ID of the track.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2. Default is ``SG``.
            Allowed values: ``HK``, ``JP``, ``MY``, ``SG``, ``TW``.

        Returns
        -------
        Track | None
            A Track object containing track information or None if not found.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        """
        if territory not in self._valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self._valid_territories} !"
            )

        query_url = f"{self._api_url}/tracks/{track_id}?territory={territory}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching track info for track_id: {track_id}")
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            track = response.json()
        except httpx.RequestError as e:
            logger.warning(
                f"Unexpected error while fetching track info from KKBox: {e}"
            )
            return None
        else:
            if track.get("error"):
                logger.warning(
                    f"Error response from KKBOX while fetching track info: {track.get('error')}"
                )
                return None

        album = track.get("album", {})
        artist = album.get("artist", {})
        return Track(
            album=Album(
                cover=album.get("images", [{}])[-1].get("url"),
                explicit=album.get("explicitness"),
                id=album.get("id"),
                release_date=album.get("release_date"),
                title=album.get("name"),
                url=album.get("url"),
            ),
            artists=[
                Artist(
                    id=artist.get("id"),
                    name=artist.get("name"),
                    picture=artist.get("images", [{}])[-1].get("url"),
                    url=artist.get("url"),
                )
            ],
            duration=(track.get("duration", 1000) // 1000),
            explicit=track.get("explicitness"),
            id=track.get("id"),
            isrc=track.get("isrc"),
            title=track.get("name"),
            track_number=track.get("track_number"),
            url=track.get("url"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_album(
        self,
        album_id: str,
        territory: str = "SG",
    ) -> Optional[Album]:
        """
        Retrieves album information for a given album ID. Use it if you already have the album ID from KKBox.

        Parameters
        ----------
        album_id : int
            The ID of the album.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2. Default is ``SG``.
            Allowed values: ``HK``, ``JP``, ``MY``, ``SG``, ``TW``.

        Returns
        -------
        Album | None
            An Album object containing album information or None if not found.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        """
        if territory not in self._valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self._valid_territories} !"
            )

        query_url = f"{self._api_url}/albums/{album_id}?territory={territory}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching album info for album_id: {album_id}")
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            album = response.json()
        except httpx.RequestError as e:
            logger.warning(
                f"Unexpected error while fetching album info from KKBox: {e}"
            )
            return None
        else:
            if album.get("error"):
                logger.warning(
                    f"Error response from KKBOX while fetching album info: {album.get('error')}"
                )
                return None

        artist = album.get("artist", {})
        return Album(
            artists=[
                Artist(
                    id=artist.get("id"),
                    name=artist.get("name"),
                    picture=artist.get("images", [{}])[-1].get("url"),
                    url=artist.get("url"),
                )
            ],
            cover=album.get("images", [{}])[-1].get("url"),
            explicit=album.get("explicitness"),
            id=album.get("id"),
            release_date=album.get("release_date"),
            title=album.get("name"),
            url=album.get("url"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_artist(
        self,
        artist_id: str,
        territory: str = "SG",
    ) -> Optional[Artist]:
        """
        Retrieves artist information for a given artist ID. Use it if you already have the artist ID from KKBox.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2. Default is ``SG``.
            Allowed values: ``HK``, ``JP``, ``MY``, ``SG``, ``TW``.

        Returns
        -------
        Artist | None
            An Artist object containing artist information or None if not found.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        """
        if territory not in self._valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self._valid_territories} !"
            )

        query_url = f"{self._api_url}/artists/{artist_id}?territory={territory}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching artist info for artist_id: {artist_id}")
            logger.debug(f"Query URL: {query_url}")
            assert self._session is not None
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            artist = response.json()
        except httpx.RequestError as e:
            logger.warning(
                f"Unexpected error while fetching artist info from KKBox: {e}"
            )
            return None
        else:
            if artist.get("error"):
                logger.warning(
                    f"Error response from KKBox while fetching artist info: {artist.get('error')}"
                )
                return None

        return Artist(
            id=artist.get("id"),
            name=artist.get("name"),
            picture=artist.get("images", [{}])[-1].get("url"),
            url=artist.get("url"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_html_widget(
        self,
        id: str,
        content_type: str,
        territory: str = "SG",
        widget_lang: str = "EN",
        autoplay: bool = False,
        loop: bool = False,
    ) -> str:
        """
        Return KKBOX HTML widget for "Playlist", "Album" or "Song". It does not return actual HTML code,
        the URL returned can be used in an HTML ``iframe`` with the help of ``src`` attribute.

        Parameters
        ----------
        id : str
             ``ID`` of playlist, album or track.
        content_type : str
            Content type can be ``playlist``, ``album`` or ``song``.
        territory : str, optional
            Territory code, i.e. "TW", "HK", "JP", "SG", "MY", by default "SG"
        widget_lang : str, optional
            The display language of the widget. Can be "TC", "SC", "JA", "EN", "MS", by default "EN"
        autoplay : bool, optional
            Whether to start playing music automatically in widget, by default False
        loop : bool, optional
            Repeat/loop song(s), by default False

        Returns
        -------
        str
            KKBOX HTML widget URL.
        """
        valid_content_types = ["playlist", "album", "song"]
        valid_widget_langs = ["TC", "SC", "JA", "EN", "MS"]
        if content_type not in valid_content_types:
            raise InvalidValueException(
                f"`content_type` must be one of these: {valid_content_types} !"
            )

        if territory not in self._valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self._valid_territories} !"
            )

        if widget_lang not in valid_widget_langs:
            raise InvalidValueException(
                f"`widget_lang` must be one of these: {valid_widget_langs} !"
            )

        return f"https://widget.kkbox.com/v1/?id={id}&type={content_type}&terr={territory}&lang={widget_lang}&autoplay={autoplay}&loop={loop}"
