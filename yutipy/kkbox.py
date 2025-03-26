import base64
import os
import time
from pprint import pprint
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
from yutipy.models import MusicInfo
from yutipy.utils.cheap_utils import are_strings_similar, is_valid_string

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
        self, client_id: str = KKBOX_CLIENT_ID, client_secret: str = KKBOX_CLIENT_SECRET
    ) -> None:
        """
        Initializes the KKBox class and sets up the session.

        Parameters
        ----------
        client_id : str, optional
            The Client ID for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_ID`` from .env file.
        client_secret : str, optional
            The Client secret for the KKBOX Open API. Defaults to ``KKBOX_CLIENT_SECRET`` from .env file.
        """
        if not client_id or not client_secret:
            raise KKBoxException(
                "Failed to read `KKBOX_CLIENT_ID` and/or `KKBOX_CLIENT_SECRET` from environment variables. Client ID and Client Secret must be provided."
            )

        self.client_id = client_id
        self.client_secret = client_secret
        self._session = requests.Session()
        self.api_url = "https://api.kkbox.com/v1.1"
        self.__header, self.__expires_in = self.__authenticate()
        self.__start_time = time.time()
        self._is_session_closed = False
        self.valid_territories = ["HK", "JP", "MY", "SG", "TW"]
        self.normalize_non_english = True
        self._translation_session = requests.Session()

    def __enter__(self):
        """Enters the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exits the runtime context related to this object."""
        self.close_session()

    def close_session(self) -> None:
        """Closes the current session."""
        if not self.is_session_closed:
            self._session.close()
            self._translation_session.close()
            self._is_session_closed = True

    @property
    def is_session_closed(self) -> bool:
        """Checks if the session is closed."""
        return self._is_session_closed

    def __authenticate(self) -> tuple:
        """
        Authenticates with the KKBOX Open API and returns the authorization header.

        Returns
        -------
        dict
            The authorization header.
        """
        try:
            token, expires_in = self.__get_access_token()
            return {"Authorization": f"Bearer {token}"}, expires_in
        except Exception as e:
            raise AuthenticationException(
                "Failed to authenticate with KKBOX Open API"
            ) from e

    def __get_access_token(self) -> tuple:
        """
        Gets the KKBOX Open API token.

        Returns
        -------
        str
            The KKBOX Open API token.
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
            response = self._session.post(
                url=url, headers=headers, data=data, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")

        try:
            response_json = response.json()
            return response_json.get("access_token"), response_json.get("expires_in")
        except (KeyError, ValueError) as e:
            raise InvalidResponseException(f"Invalid response received: {e}")

    def __refresh_token_if_expired(self):
        """Refreshes the token if it has expired."""
        if time.time() - self.__start_time >= self.__expires_in:
            self.__header, self.__expires_in = self.__authenticate()
            self.__start_time = time.time()

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

        self.normalize_non_english = normalize_non_english

        self.__refresh_token_if_expired()

        query = (
            f"?q={artist} - {song}&type=track,album&territory={territory}&limit={limit}"
        )
        query_url = f"{self.api_url}/search{query}"

        try:
            response = self._session.get(query_url, headers=self.__header, timeout=30)
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

        if territory not in self.valid_territories:
            raise InvalidValueException(
                f"`territory` must be one of these: {self.valid_territories} !"
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
            use_translation=self.normalize_non_english,
            translation_session=self._translation_session,
        ):
            return None

        artists_name = track["album"]["artist"]["name"]
        matching_artists = (
            artists_name
            if are_strings_similar(
                artists_name,
                artist,
                use_translation=self.normalize_non_english,
                translation_session=self._translation_session,
            )
            else None
        )

        if matching_artists:
            return MusicInfo(
                album_art=track["album"]["images"][2]["url"],
                album_title=track["album"]["name"],
                album_type=None,
                artists=artists_name,
                genre=None,
                id=track["id"],
                isrc=track["isrc"],
                lyrics=None,
                release_date=track["album"]["release_date"],
                tempo=None,
                title=track["name"],
                type="track",
                upc=None,
                url=track["url"],
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
            use_translation=self.normalize_non_english,
            translation_session=self._translation_session,
        ):
            return None

        artists_name = album["artist"]["name"]
        matching_artists = (
            artists_name
            if are_strings_similar(
                artists_name,
                artist,
                use_translation=self.normalize_non_english,
                translation_session=self._translation_session,
            )
            else None
        )

        if matching_artists:
            return MusicInfo(
                album_art=album["images"][2]["url"],
                album_title=album["name"],
                album_type=None,
                artists=artists_name,
                genre=None,
                id=album["id"],
                isrc=None,
                lyrics=None,
                release_date=album["release_date"],
                tempo=None,
                title=album["name"],
                type="album",
                upc=None,
                url=album["url"],
            )

        return None


if __name__ == "__main__":
    kkbox = KKBox(KKBOX_CLIENT_ID, KKBOX_CLIENT_SECRET)

    try:
        artist_name = input("Artist Name: ")
        song_name = input("Song Name: ")
        pprint(kkbox.search(artist_name, song_name))
    finally:
        kkbox.close_session()
