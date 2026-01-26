__all__ = ["Spotify"]

import os

import requests
from dotenv import load_dotenv

from yutipy.base_clients import BaseAuthClient, BaseClient
from yutipy.exceptions import (
    AuthenticationException,
    InvalidResponseException,
    InvalidValueException,
)
from yutipy.logger import logger
from yutipy.models import Album, Artist, CurrentlyPlaying, Track
from yutipy.utils.helpers import is_valid_string

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


class Spotify(BaseClient):
    """
    A class to interact with the Spotify API. It uses "Client Credentials" grant type (or flow).

    This class reads the ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide these values when creating an object.
    """

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        defer_load: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        client_id : str, optional
            The Client ID for the Spotify API. Defaults to ``SPOTIFY_CLIENT_ID`` from environment variable or the ``.env`` file.
        client_secret : str, optional
            The Client secret for the Spotify API. Defaults to ``SPOTIFY_CLIENT_SECRET`` from environment variable or the ``.env`` file.
        defer_load : bool, optional
            Whether to defer loading the access token during initialization, by default ``False``

        Raises
        ------
        AuthenticationException
            If the Client ID or Client Secret is not provided.
        """
        self.client_id = client_id or SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or SPOTIFY_CLIENT_SECRET

        if not self.client_id:
            raise AuthenticationException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.client_secret:
            raise AuthenticationException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        super().__init__(
            service_name="Spotify",
            service_url="https://open.spotify.com",
            api_url="https://api.spotify.com/v1",
            access_token_url="https://accounts.spotify.com/api/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            defer_load=defer_load,
        )

    def search(
        self,
        artist: str,
        song: str,
        limit: int = 10,
    ) -> list[Track | Album] | None:
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
        Optional[MusicInfo_]
            The music information if found, otherwise None.

        Raises
        ------
        InvalidValueException
            If the input values are invalid.
        InvalidResponseException
            If the response from Spotify is invalid.
        """
        if not is_valid_string(artist) or not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        query = f"?q=artist:{artist} - {song}&type=track,album&limit={limit}"
        query_url = f"{self._api_url}/search{query}"

        self._refresh_access_token()
        try:
            logger.info(
                f"Searching Spotify for `artist='{artist}'` and `song='{song}'`"
            )
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(
                query_url,
                headers=self._authorization_header(),
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            results = response.json()
        except requests.RequestException as e:
            logger.warning(f"Unexpected error while searching Spotify: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )

        tracks = results.get("tracks", {}).get("items", [{}])
        albums = results.get("albums", {}).get("items", [{}])
        mapped_results: list[Track | Album] = []

        for item in tracks:
            album = item.get("album", {})
            artists = item.get("artists", [{}])
            track = Track(
                album=Album(
                    cover=album.get("images", [{}])[0].get("url"),
                    id=album.get("id"),
                    release_date=album.get("release_date"),
                    title=album.get("name"),
                    total_tracks=album.get("total_tracks"),
                    type=album.get("album_type"),
                    url=album.get("external_urls", {}).get("spotify"),
                ),
                artists=[
                    Artist(
                        id=artist.get("id"),
                        name=artist.get("name"),
                        url=artist.get("external_urls", {}).get("spotify"),
                    )
                    for artist in artists
                ],
                duration=item.get("duration_ms", 1000) // 1000,
                explicit=item.get("explicit"),
                id=item.get("id"),
                isrc=item.get("external_ids", {}).get("isrc"),
                title=item.get("name"),
                track_number=item.get("track_number"),
                url=item.get("external_urls", {}).get("spotify"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results.append(track)

        for item in albums:
            artists = item.get("artists", [{}])
            album = Album(
                artists=[
                    Artist(
                        id=artist.get("id"),
                        name=artist.get("name"),
                        url=artist.get("external_urls", {}).get("spotify"),
                    )
                    for artist in artists
                ],
                cover=item.get("images", [{}])[0].get("url"),
                id=item.get("id"),
                release_date=item.get("release_date"),
                title=item.get("name"),
                total_tracks=item.get("total_tracks"),
                type=item.get("album_type"),
                url=item.get("external_urls", {}).get("spotify"),
                service_name=self.service_name,
                service_url=self.service_url,
            )
            mapped_results.append(album)

        return mapped_results if mapped_results else None

    def get_track(self, track_id: str) -> Track | None:
        """
        Retrieves track information for a given track ID. Use it if you already have the track ID from Spotify.

        Parameters
        ----------
        track_id : str
            The ID of the track.

        Returns
        -------
        Track | None
            A Track object containing track information or None if not found.

        Raises
        ------
        InvalidResponseException
            If the response from Spotify is invalid.
        """
        query_url = f"{self._api_url}/tracks/{track_id}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching track info for track_id: {track_id}")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            track = response.json()
        except requests.RequestException as e:
            logger.warning(
                f"Unexpected error while fetching track info from Spotify: {e}"
            )
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )
        else:
            if track.get("error"):
                logger.warning(
                    f"Error response from Spotify while fetching track info: {track.get('error')}"
                )
                return None

        album = track.get("album", {})
        artists = album.get("artist", [{}])
        return Track(
            album=Album(
                cover=album.get("images", [{}])[0].get("url"),
                id=album.get("id"),
                release_date=album.get("release_date"),
                title=album.get("name"),
                total_tracks=album.get("total_tracks"),
                type=album.get("album_type"),
                url=album.get("external_urls", {}).get("spotify"),
            ),
            artists=[
                Artist(
                    id=artist.get("id"),
                    name=artist.get("name"),
                    url=artist.get("external_urls", {}).get("spotify"),
                )
                for artist in artists
            ],
            duration=(track.get("duration_ms", 1000) // 1000),
            explicit=track.get("explicit"),
            id=track.get("id"),
            isrc=track.get("external_ids", {}).get("isrc"),
            title=track.get("name"),
            track_number=track.get("track_number"),
            url=track.get("external_urls", {}).get("spotify"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_album(self, album_id: str) -> Album | None:
        """
        Retrieves album information for a given album ID. Use it if you already have the album ID from Spotify.

        Parameters
        ----------
        album_id : str
            The ID of the album.

        Returns
        -------
        Album | None
            An Album object containing album information or None if not found.

        Raises
        ------
        InvalidResponseException
            If the response from Spotify is invalid.
        """
        query_url = f"{self._api_url}/albums/{album_id}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching album info for album_id: {album_id}")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            album = response.json()
        except requests.RequestException as e:
            logger.warning(
                f"Unexpected error while fetching album info from Spotify: {e}"
            )
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )
        else:
            if album.get("error"):
                logger.warning(
                    f"Error response from Spotify while fetching album info: {album.get('error')}"
                )
                return None

        artists = album.get("artist", [{}])
        tracks = album.get("tracks", [{}])
        return Album(
            artists=[
                Artist(
                    id=artist.get("id"),
                    name=artist.get("name"),
                    url=artist.get("external_urls", {}).get("spotify"),
                )
                for artist in artists
            ],
            cover=album.get("images", [{}])[0].get("url"),
            id=album.get("id"),
            label=album.get("label"),
            release_date=album.get("release_date"),
            title=album.get("name"),
            total_tracks=album.get("total_tracks"),
            tracks=[
                Track(
                    artists=[
                        Artist(
                            id=artist.get("id"),
                            name=artist.get("name"),
                            url=artist.get("external_urls", {}).get("spotify"),
                        )
                        for artist in track.get("artists", [{}])
                    ],
                    duration=track.get("duration_ms", 1000) // 1000,
                    explicit=track.get("explicit"),
                    id=track.get("id"),
                    title=track.get("name"),
                    track_number=track.get("track_number"),
                    url=track.get("external_urls", {}).get("spotify"),
                )
                for track in tracks
            ],
            type=album.get("album_type"),
            upc=album.get("external_ids", {}).get("upc"),
            url=album.get("external_urls", {}).get("spotify"),
            service_name=self.service_name,
            service_url=self.service_url,
        )

    def get_artist(self, artist_id: str) -> Artist | None:
        """
        Retrieves artist information for a given artist ID. Use it if you already have the artist ID from Spotify.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.

        Returns
        -------
        Artist | None
            An Artist object containing artist information or None if not found.

        Raises
        ------
        InvalidResponseException
            If the response from Spotify is invalid.
        """
        query_url = f"{self._api_url}/artists/{artist_id}"

        self._refresh_access_token()
        try:
            logger.info(f"Fetching artist info for artist_id: {artist_id}")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing Response JSON.")
            artist = response.json()
        except requests.RequestException as e:
            logger.warning(
                f"Unexpected error while fetching artist info from Spotify: {e}"
            )
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )
        else:
            if artist.get("error"):
                logger.warning(
                    f"Error response from Spotify while fetching artist info: {artist.get('error')}"
                )
                return None

        return Artist(
            genres=artist.get("genres"),
            id=artist.get("id"),
            name=artist.get("name"),
            picture=artist.get("images", [{}])[0].get("url"),
            url=artist.get("external_urls", {}).get("spotify"),
            service_name=self.service_name,
            service_url=self.service_url,
        )


class SpotifyAuth(BaseAuthClient):
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

        Raises
        ------
        AuthenticationException
            If the Client ID or Client Secret is not provided.
        """
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI")
        self.scopes = scopes

        if not self.client_id:
            raise AuthenticationException(
                "Client ID was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.client_secret:
            raise AuthenticationException(
                "Client Secret was not found. Set it in environment variable or directly pass it when creating object."
            )

        if not self.redirect_uri:
            raise AuthenticationException(
                "No redirect URI was provided! Set it in environment variable or directly pass it when creating object."
            )

        if not scopes:
            logger.warning(
                "No scopes were provided. Authorization will only grant access to publicly available information."
            )
        else:
            self.scopes = " ".join(scopes)

        super().__init__(
            service_name="Spotify",
            service_url="https://open.spotify.com",
            api_url="https://api.spotify.com/v1/me",
            access_token_url="https://accounts.spotify.com/api/token",
            user_auth_url="https://accounts.spotify.com/authorize",
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scopes=self.scopes,
            defer_load=defer_load,
        )

    def get_user_profile(self) -> dict | None:
        """
        Fetches the user's display name and profile images.

        Notes
        -----
        - ``user-read-email`` and ``user-read-private`` scopes are required to access user profile information.

        Returns
        -------
        dict | None
            A dictionary containing the user's display name and profile images.

        Raises
        ------
        InvalidResponseException
            If the response from Spotify is invalid.
        """
        self._refresh_access_token()
        query_url = self._api_url
        header = self._authorization_header()

        try:
            logger.info("Fetching user's Spotify profile information.")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(
                query_url,
                headers=header,
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            result = response.json()
        except requests.RequestException as e:
            logger.warning(
                f"Unexpected error while fetching user's Spotify profile: {e}"
            )
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )

        return {
            "display_name": result.get("display_name"),
            "images": result.get("images", []),
            "url": result.get("external_urls", {}).get("spotify"),
        }

    def get_currently_playing(self) -> CurrentlyPlaying | None:
        """
        Fetches information about the currently playing track for the authenticated user.

        Returns
        -------
        CurrentlyPlaying | None
            An instance of the ``CurrentlyPlaying`` model containing details about the currently
            playing track if available, or ``None`` if no track is currently playing or an
            error occurs.

        Notes
        -----
        - The user must have granted the necessary permissions (e.g., `user-read-currently-playing` scope) for this method to work.
        - If the API response does not contain the expected data, the method will return `None`.

        """
        self._refresh_access_token()
        query_url = f"{self._api_url}/player/currently-playing"
        header = self._authorization_header()

        try:
            logger.info("Fetching user's Spotify listening activity.")
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(
                query_url,
                headers=header,
                timeout=30,
            )
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            result = response.json()
        except requests.RequestException as e:
            logger.warning(
                f"Unexpected error while getting user's Spotify activity: {e}"
            )
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from Spotify: {e}"
            )
        else:
            if response.status_code == 204:  # no content
                logger.info("Requested user is currently not listening to any music.")
                return None

        item = result.get("item")
        if not item:
            return None

        album = item.get("album", {})
        artists = item.get("artists", [])
        track_artists = [
            Artist(
                id=artist.get("id"),
                name=artist.get("name"),
                url=artist.get("external_urls", {}).get("spotify"),
            )
            for artist in artists
        ]
        album_artists = [
            Artist(
                id=artist.get("id"),
                name=artist.get("name"),
                url=artist.get("external_urls", {}).get("spotify"),
            )
            for artist in album.get("artists", [])
        ]
        track_album = Album(
            artists=album_artists,
            cover=(
                album.get("images", [{}])[0].get("url") if album.get("images") else None
            ),
            id=album.get("id"),
            release_date=album.get("release_date"),
            title=album.get("name"),
            total_tracks=album.get("total_tracks"),
            type=album.get("album_type"),
            url=album.get("external_urls", {}).get("spotify"),
        )

        return CurrentlyPlaying(
            album=track_album,
            artists=track_artists,
            duration=item.get("duration_ms", 1000) // 1000,
            explicit=item.get("explicit"),
            id=item.get("id"),
            isrc=item.get("external_ids", {}).get("isrc"),
            preview_url=item.get("preview_url"),
            release_date=album.get("release_date"),
            title=item.get("name"),
            track_number=item.get("track_number"),
            url=item.get("external_urls", {}).get("spotify"),
            timestamp=result.get("timestamp"),
            progress=result.get("progress_ms", 1000) // 1000,
            is_playing=result.get("is_playing"),
            currently_playing_type=result.get("currently_playing_type"),
            service_name=self.service_name,
            service_url=self.service_url,
        )
