__all__ = ["KKBox", "KKBoxException"]

import base64
import os
from dataclasses import asdict
from pprint import pprint
from time import time
from typing import Optional, Union

import requests
from dotenv import load_dotenv

from yutipy.exceptions import (
    AuthenticationException,
    InvalidResponseException,
    InvalidValueException,
    KKBoxException,
    NetworkException,
)
from yutipy.logger import logger
from yutipy.models import MusicInfo
from yutipy.utils.helpers import are_strings_similar, is_valid_string

load_dotenv()

KKBOX_CLIENT_ID = os.getenv("KKBOX_CLIENT_ID")
KKBOX_CLIENT_SECRET = os.getenv("KKBOX_CLIENT_SECRET")


class KKBox:
    """
    A class to interact with KKBOX Open API.

    This class reads the ``KKBOX_CLIENT_ID`` and ``KKBOX_CLIENT_SECRET`` from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide these values when creating an object.
    """

    def __init__(
        self, client_id: str = None, client_secret: str = None, defer_load: bool = False
    ) -> None:
        """
        Initializes the KKBox class and sets up the session.

        Parameters
        ----------
        client_id : str, optional
            The Client ID for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_ID`` from .env file.
        client_secret : str, optional
            The Client secret for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_SECRET`` from .env file.
        defer_load : bool, optional
            Whether to defer loading the access token during initialization. Default is ``False``.
        """
        self.client_id = client_id or KKBOX_CLIENT_ID
        self.client_secret = client_secret or KKBOX_CLIENT_SECRET

        if not self.client_id:
            raise KKBoxException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.client_secret:
            raise KKBoxException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        self.defer_load = defer_load

        self._is_session_closed = False
        self._normalize_non_english = True
        self._valid_territories = ["HK", "JP", "MY", "SG", "TW"]

        self.api_url = "https://api.kkbox.com/v1.1"
        self.__access_token = None
        self.__token_expires_in = None
        self.__token_requested_at = None
        self.__session = requests.Session()
        self.__translation_session = requests.Session()

        if not defer_load:
            # Attempt to load access token during initialization if not deferred
            token_info = None
            try:
                token_info = self.load_access_token()
            except NotImplementedError:
                logger.warning(
                    "`load_access_token` is not implemented. Falling back to in-memory storage and requesting new access token."
                )
            finally:
                if not token_info:
                    token_info = self.__get_access_token()
                self.__access_token = token_info.get("access_token")
                self.__token_expires_in = token_info.get("expires_in")
                self.__token_requested_at = token_info.get("requested_at")

                try:
                    self.save_access_token(token_info)
                except NotImplementedError:
                    logger.warning(
                        "`save_access_token` is not implemented, falling back to in-memory storage. Access token will not be saved."
                    )
        else:
            logger.warning(
                "`defer_load` is set to `True`. Make sure to call `load_token_after_init()`."
            )

    def __enter__(self):
        """Enters the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exits the runtime context related to this object."""
        self.close_session()

    def close_session(self) -> None:
        """Closes the current session."""
        if not self.is_session_closed:
            self.__session.close()
            self.__translation_session.close()
            self._is_session_closed = True

    @property
    def is_session_closed(self) -> bool:
        """Checks if the session is closed."""
        return self._is_session_closed

    def load_token_after_init(self):
        """
        Explicitly load the access token after initialization.
        This is useful when ``defer_load`` is set to ``True`` during initialization.
        """
        token_info = None
        try:
            token_info = self.load_access_token()
        except NotImplementedError:
            logger.warning(
                "`load_access_token` is not implemented. Falling back to in-memory storage and requesting new access token."
            )
        finally:
            if not token_info:
                token_info = self.__get_access_token()
            self.__access_token = token_info.get("access_token")
            self.__token_expires_in = token_info.get("expires_in")
            self.__token_requested_at = token_info.get("requested_at")

            try:
                self.save_access_token(token_info)
            except NotImplementedError:
                logger.warning(
                    "`save_access_token` is not implemented, falling back to in-memory storage. Access token will not be saved."
                )

    def __authorization_header(self) -> dict:
        """
        Generates the authorization header for Spotify API requests.

        Returns
        -------
        dict
            A dictionary containing the Bearer token for authentication.
        """
        return {"Authorization": f"Bearer {self.__access_token}"}

    def __get_access_token(self) -> dict:
        """
        Gets the KKBOX Open API access token information.

        Returns
        -------
        str
            The KKBOX Open API access token, with additional information such as expires in, etc.
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        url = " https://account.kkbox.com/oauth2/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        try:
            logger.info("Authenticating with KKBOX Open API")
            response = self.__session.post(
                url=url, headers=headers, data=data, timeout=30
            )
            logger.debug(f"Authentication response status code: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error during KKBOX authentication: {e}")
            raise NetworkException(f"Network error occurred: {e}")

        if response.status_code == 200:
            response_json = response.json()
            response_json["requested_at"] = time()
            return response_json
        else:
            raise InvalidResponseException(
                f"Invalid response received: {response.json()}"
            )

    def __refresh_access_token(self):
        """Refreshes the token if it has expired."""
        if time() - self.__token_requested_at >= self.__token_expires_in:
            token_info = self.__get_access_token()

            try:
                self.save_access_token(token_info)
            except NotImplementedError as e:
                logger.warning(e)

            self.__access_token = token_info.get("access_token")
            self.__token_expires_in = token_info.get("expires_in")
            self.__token_requested_at = token_info.get("requested_at")

        logger.info("The access token is still valid, no need to refresh.")

    def save_access_token(self, token_info: dict) -> None:
        """
        Saves the access token and related information.

        This method must be overridden in a subclass to persist the access token and other
        related information (e.g., expiration time). If not implemented,
        the access token will not be saved, and it will be requested each time the
        application restarts.

        Parameters
        ----------
        token_info : dict
            A dictionary containing the access token and related information, such as
            refresh token, expiration time, etc.

        Raises
        ------
        NotImplementedError
            If the method is not overridden in a subclass.
        """
        raise NotImplementedError(
            "The `save_access_token` method must be overridden in a subclass to save the access token and related information. "
            "If not implemented, access token information will not be persisted, and users will need to re-authenticate after application restarts."
        )

    def load_access_token(self) -> Union[dict, None]:
        """
        Loads the access token and related information.

        This method must be overridden in a subclass to retrieve the access token and other
        related information (e.g., expiration time) from persistent storage.
        If not implemented, the access token will not be loaded, and it will be requested
        each time the application restarts.

        Returns
        -------
        dict | None
            A dictionary containing the access token and related information, such as
            refresh token, expiration time, etc., or None if no token is found.

        Raises
        ------
        NotImplementedError
            If the method is not overridden in a subclass.
        """
        raise NotImplementedError(
            "The `load_access_token` method must be overridden in a subclass to load access token and related information. "
            "If not implemented, access token information will not be loaded, and users will need to re-authenticate after application restarts."
        )

    def search(
        self,
        artist: str,
        song: str,
        territory: str = "TW",
        limit: int = 10,
        normalize_non_english: bool = True,
    ) -> Optional[MusicInfo]:
        """
        Searches for a song by artist and title.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        territory : str
            Two-letter country codes from ISO 3166-1 alpha-2.
            Allowed values: ``HK``, ``JP``, ``MY``, ``SG``, ``TW``.
        limit: int, optional
            The number of items to retrieve from API. ``limit >=1 and <= 50``. Default is ``10``.
        normalize_non_english : bool, optional
            Whether to normalize non-English characters for comparison. Default is ``True``.

        Returns
        -------
        Optional[MusicInfo_]
            The music information if found, otherwise None.
        """
        if not is_valid_string(artist) or not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        self._normalize_non_english = normalize_non_english

        self.__refresh_access_token()

        query = (
            f"?q={artist} - {song}&type=track,album&territory={territory}&limit={limit}"
        )
        query_url = f"{self.api_url}/search{query}"

        logger.info(f"Searching KKBOX for `artist='{artist}'` and `song='{song}'`")
        logger.debug(f"Query URL: {query_url}")

        try:
            response = self.__session.get(
                query_url, headers=self.__authorization_header(), timeout=30
            )
            logger.debug(f"Parsing response JSON: {response.json()}")
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")

        if response.status_code != 200:
            raise KKBoxException(f"Failed to search for music: {response.json()}")

        return self._find_music_info(artist, song, response.json())

    def get_html_widget(
        self,
        id: str,
        content_type: str,
        territory: str = "TW",
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
            Territory code, i.e. "TW", "HK", "JP", "SG", "MY", by default "TW"
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

    def _find_music_info(
        self, artist: str, song: str, response_json: dict
    ) -> Optional[MusicInfo]:
        """
        Finds the music information from the search results.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        response_json : dict
            The JSON response from the API.

        Returns
        -------
        Optional[MusicInfo]
            The music information if found, otherwise None.
        """
        try:
            for track in response_json["tracks"]["data"]:
                music_info = self._find_track(song, artist, track)
                if music_info:
                    return music_info
        except KeyError:
            pass

        try:
            for album in response_json["albums"]["data"]:
                music_info = self._find_album(song, artist, album)
                if music_info:
                    return music_info
        except KeyError:
            pass

        logger.warning(
            f"No matching results found for artist='{artist}' and song='{song}'"
        )
        return None

    def _find_track(self, song: str, artist: str, track: dict) -> Optional[MusicInfo]:
        """
        Finds the track information from the search results.

        Parameters
        ----------
        song : str
            The title of the song.
        artist : str
            The name of the artist.
        track : dict
            A single track from the search results.

        Returns
        -------
        Optional[MusicInfo]
            The music information if found, otherwise None.
        """
        if not are_strings_similar(
            track["name"],
            song,
            use_translation=self._normalize_non_english,
            translation_session=self.__translation_session,
        ):
            return None

        artists_name = track.get("album", {}).get("artist", {}).get("name")
        matching_artists = (
            artists_name
            if are_strings_similar(
                artists_name,
                artist,
                use_translation=self._normalize_non_english,
                translation_session=self.__translation_session,
            )
            else None
        )

        if matching_artists:
            return MusicInfo(
                album_art=track.get("album", {}).get("images", [])[2]["url"],
                album_title=track.get("album", {}).get("name"),
                album_type=None,
                artists=artists_name,
                genre=None,
                id=track.get("id"),
                isrc=track.get("isrc"),
                lyrics=None,
                release_date=track.get("album", {}).get("release_date"),
                tempo=None,
                title=track.get("name"),
                type="track",
                upc=None,
                url=track.get("url"),
            )

        return None

    def _find_album(self, song: str, artist: str, album: dict) -> Optional[MusicInfo]:
        """
        Finds the album information from the search results.

        Parameters
        ----------
        song : str
            The title of the song.
        artist : str
            The name of the artist.
        album : dict
            A single album from the search results.

        Returns
        -------
        Optional[MusicInfo]
            The music information if found, otherwise None.
        """
        if not are_strings_similar(
            album["name"],
            song,
            use_translation=self._normalize_non_english,
            translation_session=self.__translation_session,
        ):
            return None

        artists_name = album.get("artist", {}).get("name")
        matching_artists = (
            artists_name
            if are_strings_similar(
                artists_name,
                artist,
                use_translation=self._normalize_non_english,
                translation_session=self.__translation_session,
            )
            else None
        )

        if matching_artists:
            return MusicInfo(
                album_art=album.get("images", [])[2]["url"],
                album_title=album.get("name"),
                album_type=None,
                artists=artists_name,
                genre=None,
                id=album.get("id"),
                isrc=None,
                lyrics=None,
                release_date=album.get("release_date"),
                tempo=None,
                title=album.get("name"),
                type="album",
                upc=None,
                url=album.get("url"),
            )

        return None


if __name__ == "__main__":
    import logging

    from yutipy.logger import enable_logging

    enable_logging(level=logging.DEBUG)
    kkbox = KKBox(KKBOX_CLIENT_ID, KKBOX_CLIENT_SECRET)

    try:
        artist_name = input("Artist Name: ")
        song_name = input("Song Name: ")
        result = kkbox.search(artist_name, song_name)
        pprint(asdict(result))
    finally:
        kkbox.close_session()
