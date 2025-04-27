__all__ = ["Spotify", "SpotifyException", "SpotifyAuthException"]

import base64
import os
import secrets
import webbrowser
from pprint import pprint
from time import time
from typing import Optional, Union
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from yutipy.exceptions import (
    AuthenticationException,
    InvalidResponseException,
    InvalidValueException,
    NetworkException,
    SpotifyAuthException,
    SpotifyException,
)
from yutipy.logger import logger
from yutipy.models import MusicInfo, UserPlaying
from yutipy.utils.helpers import (
    are_strings_similar,
    guess_album_type,
    is_valid_string,
    separate_artists,
)

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


class Spotify:
    """
    A class to interact with the Spotify API. It uses "Client Credentials" grant type (or flow).

    This class reads the ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide these values when creating an object.
    """

    def __init__(
        self, client_id: str = None, client_secret: str = None, defer_load: bool = False
    ) -> None:
        """
        Initializes the Spotify class (using Client Credentials grant type/flow) and sets up the session.

        Parameters
        ----------
        client_id : str, optional
            The Client ID for the Spotify API. Defaults to ``SPOTIFY_CLIENT_ID`` from environment variable or the ``.env`` file.
        client_secret : str, optional
            The Client secret for the Spotify API. Defaults to ``SPOTIFY_CLIENT_SECRET`` from environment variable or the ``.env`` file.
        defer_load : bool, optional
            Whether to defer loading the access token during initialization. Default is ``False``.
        """

        self.client_id = client_id or SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or SPOTIFY_CLIENT_SECRET

        if not self.client_id:
            raise SpotifyException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.client_secret:
            raise SpotifyException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        self.defer_load = defer_load

        self._is_session_closed = False
        self._normalize_non_english = True

        self.__api_url = "https://api.spotify.com/v1"
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
        """Closes the current session(s)."""
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
        Gets the Spotify API access token information.

        Returns
        -------
        dict
            The Spotify API access token, with additional information such as expires in, etc.
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        try:
            logger.info(
                "Authenticating with Spotify API using Client Credentials grant type."
            )
            response = self.__session.post(
                url=url, headers=headers, data=data, timeout=30
            )
            logger.debug(f"Authentication response status code: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error during Spotify authentication: {e}")
            raise NetworkException(f"Network error occurred: {e}")

        if response.status_code == 200:
            response_json = response.json()
            response_json["requested_at"] = time()
            return response_json
        else:
            raise AuthenticationException(
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

        music_info = None
        artist_ids = None
        queries = [
            f"?q=artist:{artist} track:{song}&type=track&limit={limit}",
            f"?q=artist:{artist} album:{song}&type=album&limit={limit}",
        ]

        for query in queries:
            if music_info:
                return music_info

            self.__refresh_access_token()

            query_url = f"{self.__api_url}/search{query}"

            logger.info(
                f"Searching Spotify for `artist='{artist}'` and `song='{song}'`"
            )
            logger.debug(f"Query URL: {query_url}")

            try:
                response = self.__session.get(
                    query_url, headers=self.__authorization_header(), timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise NetworkException(f"Network error occurred: {e}")

            if response.status_code != 200:
                raise SpotifyException(f"Failed to search for music: {response.json()}")

            artist_ids = artist_ids if artist_ids else self._get_artists_ids(artist)
            music_info = self._find_music_info(
                artist, song, response.json(), artist_ids
            )

        return music_info

    def search_advanced(
        self,
        artist: str,
        song: str,
        isrc: str = None,
        upc: str = None,
        limit: int = 1,
        normalize_non_english: bool = True,
    ) -> Optional[MusicInfo]:
        """
        Searches for a song by artist, title, ISRC, or UPC.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        isrc : str, optional
            The ISRC of the track.
        upc : str, optional
            The UPC of the album.
        limit: int, optional
            The number of items to retrieve from API. ``limit >=1 and <= 50``. Default is ``1``.
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

        if isrc:
            query = f"?q={artist} {song} isrc:{isrc}&type=track&limit={limit}"
        elif upc:
            query = f"?q={artist} {song} upc:{upc}&type=album&limit={limit}"
        else:
            raise InvalidValueException("ISRC or UPC must be provided.")

        query_url = f"{self.__api_url}/search{query}"
        try:
            response = self.__session.get(
                query_url, headers=self.__authorization_header(), timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")

        if response.status_code != 200:
            raise SpotifyException(
                f"Failed to search music with ISRC/UPC: {response.json()}"
            )

        artist_ids = self._get_artists_ids(artist)
        return self._find_music_info(artist, song, response.json(), artist_ids)

    def _get_artists_ids(self, artist: str) -> Union[list, None]:
        """
        Retrieves the IDs of the artists.

        Parameters
        ----------
        artist : str
            The name of the artist.

        Returns
        -------
        Union[list, None]
            A list of artist IDs or None if not found.
        """
        artist_ids = []
        for name in separate_artists(artist):
            query_url = f"{self.__api_url}/search?q={name}&type=artist&limit=5"
            try:
                response = self.__session.get(
                    query_url, headers=self.__authorization_header(), timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise NetworkException(f"Network error occurred: {e}")

            if response.status_code != 200:
                return None

            artist_ids.extend(
                artist["id"] for artist in response.json()["artists"]["items"]
            )
        return artist_ids

    def _find_music_info(
        self, artist: str, song: str, response_json: dict, artist_ids: list
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
        artist_ids : list
            A list of artist IDs.

        Returns
        -------
        Optional[MusicInfo]
            The music information if found, otherwise None.
        """
        try:
            for track in response_json["tracks"]["items"]:
                music_info = self._find_track(song, artist, track, artist_ids)
                if music_info:
                    return music_info
        except KeyError:
            pass

        try:
            for album in response_json["albums"]["items"]:
                music_info = self._find_album(song, artist, album, artist_ids)
                if music_info:
                    return music_info
        except KeyError:
            pass

        logger.warning(
            f"No matching results found for artist='{artist}' and song='{song}'"
        )
        return None

    def _find_track(
        self, song: str, artist: str, track: dict, artist_ids: list
    ) -> Optional[MusicInfo]:
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
        artist_ids : list
            A list of artist IDs.

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

        artists_name = [x["name"] for x in track["artists"]]
        matching_artists = [
            x["name"]
            for x in track["artists"]
            if are_strings_similar(
                x["name"],
                artist,
                use_translation=self._normalize_non_english,
                translation_session=self.__translation_session,
            )
            or x["id"] in artist_ids
        ]

        if matching_artists:
            return MusicInfo(
                album_art=track["album"]["images"][0]["url"],
                album_title=track["album"]["name"],
                album_type=track["album"]["album_type"],
                artists=", ".join(artists_name),
                genre=None,
                id=track["id"],
                isrc=track.get("external_ids").get("isrc"),
                lyrics=None,
                release_date=track["album"]["release_date"],
                tempo=None,
                title=track["name"],
                type="track",
                upc=None,
                url=track["external_urls"]["spotify"],
            )

        return None

    def _find_album(
        self, song: str, artist: str, album: dict, artist_ids: list
    ) -> Optional[MusicInfo]:
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
        artist_ids : list
            A list of artist IDs.

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

        artists_name = [x["name"] for x in album["artists"]]
        matching_artists = [
            x["name"]
            for x in album["artists"]
            if are_strings_similar(
                x["name"],
                artist,
                use_translation=self._normalize_non_english,
                translation_session=self.__translation_session,
            )
            or x["id"] in artist_ids
        ]

        if matching_artists:
            guess = guess_album_type(album.get("total_tracks", 1))
            guessed_right = are_strings_similar(
                album.get("album_type", "x"), guess, use_translation=False
            )

            return MusicInfo(
                album_art=album["images"][0]["url"],
                album_title=album["name"],
                album_type=album.get("album_type") if guessed_right else guess,
                artists=", ".join(artists_name),
                genre=None,
                id=album["id"],
                isrc=None,
                lyrics=None,
                release_date=album["release_date"],
                tempo=None,
                title=album["name"],
                type=album.get("type"),
                upc=None,
                url=album["external_urls"]["spotify"],
            )

        return None


class SpotifyAuth:
    """
    A class to interact with the Spotify API. It uses "Authorization Code" grant type (or flow).

    This class reads the ``SPOTIFY_CLIENT_ID``, ``SPOTIFY_CLIENT_SECRET`` and ``SPOTIFY_REDIRECT_URI``
    from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide these values when creating an object.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        scopes: list[str] = None,
        defer_load: bool = False,
    ):
        """
        Initializes the SpotifyAuth class (using Authorization Code grant type/flow) and sets up the session.

        Parameters
        ----------
        client_id : str, optional
            The Client ID for the Spotify API. Defaults to ``SPOTIFY_CLIENT_ID`` from environment variable or the ``.env`` file.
        client_secret : str, optional
            The Client secret for the Spotify API. Defaults to ``SPOTIFY_CLIENT_SECRET`` from environment variable or the ``.env`` file.
        redirect_uri : str, optional
            The Redirect URI for the Spotify API. Defaults to ``SPOTIFY_REDIRECT_URI`` from environment variable or the ``.env`` file.
        scopes : list[str], optional
            A list of scopes for the Spotify API. For example: `['user-read-email', 'user-read-private']`.
        defer_load : bool, optional
            Whether to defer loading the access token during initialization. Default is ``False``.
        """
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI")

        if not self.client_id:
            raise SpotifyAuthException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.client_secret:
            raise SpotifyAuthException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.redirect_uri:
            raise SpotifyAuthException(
                "No redirect URI was provided! Set it in environment variable or directly pass it when creating object."
            )

        self.scope = scopes
        self.defer_load = defer_load

        self._is_session_closed = False

        self.__api_url = "https://api.spotify.com/v1/me"
        self.__access_token = None
        self.__refresh_token = None
        self.__token_expires_in = None
        self.__token_requested_at = None
        self.__session = requests.Session()

        if not scopes:
            logger.warning(
                "No scopes were provided. Authorization will only grant access to publicly available information."
            )
            self.scope = None
        else:
            self.scope = " ".join(scopes)

        if not defer_load:
            # Attempt to load access token during initialization if not deferred
            try:
                token_info = self.load_access_token()
                if token_info:
                    self.__access_token = token_info.get("access_token")
                    self.__refresh_token = token_info.get("refresh_token")
                    self.__token_expires_in = token_info.get("expires_in")
                    self.__token_requested_at = token_info.get("requested_at")
                else:
                    logger.warning(
                        "No access token found during initialization. You must authenticate to obtain a new token."
                    )
            except NotImplementedError:
                logger.warning(
                    "`load_access_token` is not implemented. Falling back to in-memory storage."
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
        """Closes the current session(s)."""
        if not self.is_session_closed:
            self.__session.close()
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
        try:
            token_info = self.load_access_token()
            if token_info:
                self.__access_token = token_info.get("access_token")
                self.__refresh_token = token_info.get("refresh_token")
                self.__token_expires_in = token_info.get("expires_in")
                self.__token_requested_at = token_info.get("requested_at")
            else:
                logger.warning(
                    "No access token found. You must authenticate to obtain a new token."
                )
        except NotImplementedError:
            logger.warning(
                "`load_access_token` is not implemented. Falling back to in-memory storage."
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

    def __get_access_token(
        self,
        authorization_code: str = None,
        refresh_token: str = None,
    ) -> dict:
        """
        Gets the Spotify API access token information.

        If ``authorization_code`` provided, it will try to get a new access token from Spotify.
        Otherwise, if `refresh_token` is provided, it will refresh the access token using it
        and return new access token information.

        Returns
        -------
        dict
            The Spotify API access token, with additional information such as expires in, refresh token, etc.
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        if authorization_code:
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
            }

        if refresh_token:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.__refresh_token,
            }

        try:
            logger.info(
                "Authenticating with Spotify API using Authorization Code grant type."
            )
            response = self.__session.post(
                url=url, headers=headers, data=data, timeout=30
            )
            logger.debug(f"Authentication response status code: {response.status_code}")
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error during Spotify authentication: {e}")
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
        if not self.__access_token:
            raise SpotifyAuthException("No access token was found.")

        if time() - self.__token_requested_at >= self.__token_expires_in:
            token_info = self.__get_access_token(refresh_token=self.__refresh_token)

            try:
                self.save_access_token(token_info)
            except NotImplementedError as e:
                logger.warning(e)

            self.__access_token = token_info.get("access_token")
            self.__refresh_token = token_info.get("refresh_token")
            self.__token_expires_in = token_info.get("expires_in")
            self.__token_requested_at = token_info.get("requested_at")

        logger.info("The access token is still valid, no need to refresh.")

    @staticmethod
    def generate_state() -> str:
        """
        Generates a random state string for use in OAuth 2.0 authorization.

        This method creates a cryptographically secure, URL-safe string that can be used
        to prevent cross-site request forgery (CSRF) attacks during the authorization process.

        Returns
        -------
        str
            A random URL-safe string to be used as the state parameter in OAuth 2.0.
        """
        return secrets.token_urlsafe(16)

    def get_authorization_url(self, state: str = None, show_dialog: bool = False):
        """
        Constructs the Spotify authorization URL for user authentication.

        This method generates a URL that can be used to redirect users to Spotify's
        authorization page for user authentication.

        Parameters
        ----------
        state : str, optional
            A random string to maintain state between the request and callback.
            If not provided, no state parameter is included.

            You may use :meth:`SpotifyAuth.generate_state` method to generate one.
        show_dialog : bool, optional
            Whether or not to force the user to approve the app again if they’ve already done so.
            If ``False`` (default), a user who has already approved the application may be automatically
            redirected to the URI specified by redirect_uri. If ``True``, the user will not be automatically
            redirected and will have to approve the app again.

        Returns
        -------
        str
            The full authorization URL to redirect users for Spotify authentication.
        """
        auth_endpoint = "https://accounts.spotify.com/authorize"
        payload = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "show_dialog": show_dialog,
        }

        if self.scope:
            payload["scope"] = self.scope

        if state:
            payload["state"] = state

        return f"{auth_endpoint}?{urlencode(payload)}"

    def save_access_token(self, token_info: dict) -> None:
        """
        Saves the access token and related information.

        This method must be overridden in a subclass to persist the access token and other
        related information (e.g., refresh token, expiration time). If not implemented,
        the access token will not be saved, and users will need to re-authenticate after
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
        related information (e.g., refresh token, expiration time) from persistent storage.
        If not implemented, the access token will not be loaded, and users will need to
        re-authenticate after application restarts.

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

    def callback_handler(self, code, state, expected_state):
        """
        Handles the callback phase of the OAuth 2.0 authorization process.

        This method processes the authorization code and state returned by Spotify after the user
        has granted permission. It validates the state to prevent CSRF attacks, exchanges the
        authorization code for an access token, and saves the token for future use.

        Parameters
        ----------
        code : str
            The authorization code returned by Spotify after user authorization.
        state : str
            The state parameter returned by Spotify to ensure the request's integrity.
        expected_state : str
            The original state parameter sent during the authorization request, used to validate the response.

        Raises
        ------
        SpotifyAuthException
            If the returned state does not match the expected state.

        Notes
        -----
        - This method can be used in a web application (e.g., Flask) in the `/callback` route to handle
          successful authorization.
        - Ensure that the ``save_access_token`` and ``load_access_token`` methods are implemented in a subclass
          if token persistence is required.

        Example
        -------
        In a Flask application, you can use this method in the ``/callback`` route:

        .. code-block:: python

            @app.route('/callback')
            def callback():
                code = request.args.get('code')
                state = request.args.get('state')
                expected_state = session['state']  # Retrieve the state stored during authorization URL generation

                try:
                    spotify_auth.callback_handler(code, state, expected_state)
                    return "Authorization successful!"
                except SpotifyAuthException as e:
                    return f"Authorization failed: {e}", 400
        """
        if state != expected_state:
            raise SpotifyAuthException("state does not match!")

        token_info = None

        try:
            token_info = self.load_access_token()
        except NotImplementedError as e:
            logger.warning(e)

        if not token_info:
            token_info = self.__get_access_token(authorization_code=code)

        self.__access_token = token_info.get("access_token")
        self.__refresh_token = token_info.get("refresh_token")
        self.__token_expires_in = token_info.get("expires_in")
        self.__token_requested_at = token_info.get("requested_at")

        try:
            self.save_access_token(token_info)
        except NotImplementedError as e:
            logger.warning(e)

    def get_user_profile(self):
        """
        Fetches the user's display name and profile images.

        Notes
        -----
        - ``user-read-email`` and ``user-read-private`` scopes are required to access user profile information.

        Returns
        -------
        dict
            A dictionary containing the user's display name and profile images.
        """
        try:
            self.__refresh_access_token()
        except SpotifyAuthException:
            logger.warning(
                "No access token was found. You may authenticate the user again."
            )
            return None

        query_url = self.__api_url
        header = self.__authorization_header()

        try:
            response = self.__session.get(query_url, headers=header, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user profile: {e}")
            return None

        if response.status_code != 200:
            logger.error(f"Unexpected response: {response.json()}")
            return None

        response_json = response.json()
        return {
            "display_name": response_json.get("display_name"),
            "images": response_json.get("images", []),
        }

    def get_currently_playing(self) -> Optional[UserPlaying]:
        """
        Fetches information about the currently playing track for the authenticated user.

        This method interacts with the Spotify API to retrieve details about the track
        the user is currently listening to. It includes information such as the track's
        title, album, artists, release date, and more.

        Returns
        -------
        Optional[UserPlaying_]
            An instance of the ``UserPlaying`` model containing details about the currently
            playing track if available, or ``None`` if no track is currently playing or an
            error occurs.

        Notes
        -----
        - The user must have granted the necessary permissions (e.g., `user-read-currently-playing` scope) for this method to work.
        - If the API response does not contain the expected data, the method will return `None`.

        """
        try:
            self.__refresh_access_token()
        except SpotifyAuthException:
            logger.warning(
                "No access token was found. You may authenticate the user again."
            )
            return None

        query_url = f"{self.__api_url}/player/currently-playing"
        header = self.__authorization_header()

        try:
            response = self.__session.get(query_url, headers=header, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")

        if response.status_code == 204:
            logger.info("Requested user is currently not listening to any music.")
            return None
        if response.status_code != 200:
            try:
                logger.error(f"Unexpected response: {response.json()}")
            except requests.exceptions.JSONDecodeError:
                logger.error(
                    f"Response Code: {response.status_code}, Reason: {response.reason}"
                )
            return None

        response_json = response.json()
        result = response_json.get("item")
        if result:
            guess = guess_album_type(result.get("album", {}).get("total_tracks", 1))
            guessed_right = are_strings_similar(
                result.get("album", {}).get("album_type", "x"),
                guess,
                use_translation=False,
            )
            return UserPlaying(
                album_art=result.get("album", {}).get("images", [])[0].get("url"),
                album_title=result.get("album", {}).get("name"),
                album_type=(
                    result.get("album", {}).get("album_type")
                    if guessed_right
                    else guess
                ),
                artists=", ".join([x["name"] for x in result.get("artists", [])]),
                genre=None,
                id=result.get("id"),
                isrc=result.get("external_ids", {}).get("isrc"),
                is_playing=response_json.get("is_playing"),
                lyrics=None,
                release_date=result.get("album", {}).get("release_date"),
                tempo=None,
                title=result.get("name"),
                type=result.get("type"),
                upc=result.get("external_ids", {}).get("upc"),
                url=result.get("external_urls", {}).get("spotify"),
            )

        return None


if __name__ == "__main__":
    import logging
    from dataclasses import asdict

    from yutipy.logger import enable_logging

    enable_logging(level=logging.DEBUG)

    print("\nChoose Spotify Grant Type/Flow:")
    print("1. Client Credentials (Spotify)")
    print("2. Authorization Code (SpotifyAuth)")
    choice = input("\nEnter your choice (1 or 2): ")

    if choice == "1":
        spotify = Spotify(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

        try:
            artist_name = input("Artist Name: ")
            song_name = input("Song Name: ")
            result = spotify.search(artist_name, song_name)
            pprint(asdict(result))
        finally:
            spotify.close_session()

    elif choice == "2":
        redirect_uri = input("Enter Redirect URI: ")
        scopes = ["user-read-email", "user-read-private"]

        spotify_auth = SpotifyAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=redirect_uri,
            scopes=scopes,
        )

        try:
            state = spotify_auth.generate_state()
            auth_url = spotify_auth.get_authorization_url(state=state)
            print(f"Opening the following URL in your browser: {auth_url}")
            webbrowser.open(auth_url)

            code = input("Enter the authorization code: ")
            spotify_auth.callback_handler(code, state, state)

            user_profile = spotify_auth.get_user_profile()
            if user_profile:
                print(f"Successfully authenticated \"{user_profile['display_name']}\".")
            else:
                print("Authentication successful, but failed to fetch user profile.")
        finally:
            spotify_auth.close_session()

    else:
        print("Invalid choice. Exiting.")
