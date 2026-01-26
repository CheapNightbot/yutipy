__all__ = ["LastFm"]

import os
from typing import Optional

import requests
from dotenv import load_dotenv

from yutipy.base_clients import BaseService
from yutipy.exceptions import AuthenticationException, InvalidResponseException
from yutipy.logger import logger

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


class LastFm(BaseService):
    """
    A class to interact with the Last.fm API for fetching user music data.

    This class reads the ``LASTFM_API_KEY`` from environment variables or the ``.env`` file by default.
    Alternatively, you can manually provide this values when creating an object.
    """

    def __init__(self, api_key: str = None):
        """
        Parameters
        ----------
        lastfm_api_key : str, optional
            The Lastfm API Key (<https://www.last.fm/api>). Defaults to ``LASTFM_API_KEY`` from environment variable or the ``.env`` file.

        Raises
        ------
        AuthenticationException
            If the Lastfm API key is not provided or found in environment variables.
        """
        self.api_key = api_key or LASTFM_API_KEY
        if not self.api_key:
            raise AuthenticationException(
                "Lastfm API key was not found. Set it in environment variable or directly pass it when creating object."
            )

        super().__init__(
            service_name="Last.fm",
            service_url="https://www.last.fm",
            api_url="https://ws.audioscrobbler.com/2.0",
        )

    def get_user_profile(self, username: str) -> Optional[dict]:
        """
        Fetches the user profile information for the provided username.

        Parameters
        ----------
        username : str
            The Last.fm username to fetch profile information for.

        Returns
        -------
        dict | None
            A dictionary containing the user's profile information or ``None`` if username does not exist.
        """
        query = (
            f"?method=user.getinfo&user={username}&api_key={self.api_key}&format=json"
        )
        query_url = self._api_url + query

        try:
            logger.info(f"Fetching profile for Last.fm user: {username}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON")
            result = response.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch user profile: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Invalid response received from Last.fm API: {e}"
            )

        user = result.get("user", {})
        return {
            "account_type": user.get("type"),
            "avatar": user.get("image", [{}])[-1].get("#text"),
            "name": user.get("realname"),
            "username": user.get("name"),
            "url": user.get("url"),
        }

    def get_currently_playing(self, username: str) -> Optional[dict]:
        """
        Fetches information about the currently playing track for a user.

        Parameters
        ----------
        username : str
            The Last.fm username to fetch data for.

        Returns
        -------
        dict | None
            A dictionary containing details about the currently
            playing track if available, or ``None`` if the request fails or no data is available.
        """
        query = f"?method=user.getrecenttracks&user={username}&limit=1&api_key={self.api_key}&format=json"
        query_url = self._api_url + query

        try:
            logger.info(
                f"Fetching currently playing music for Last.fm user: {username}"
            )
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON")
            result = response.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch user profile: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Invalid response received from Last.fm API: {e}"
            )
        else:
            if not result:
                return

        # Whether the user currently scrobbling or not..
        currently_playing = result.get("@attr", {}).get("nowplaying", "false") == "true"
        if currently_playing:
            return {
                "album": result.get("album", {}).get("#text"),
                "artist": result.get("artist", {}).get("#text"),
                "cover": result.get("image", [{}])[-1].get("#text"),
                "scrobbling_now": True,
                "title": result.get("name"),
                "url": result.get("url"),
            }

        # UNIX timestamp and datetime (in UTC) when user last scrobbled..
        last_played_uts = result.get("date", {}).get("uts")
        last_played_dt = result.get("date", {}).get("#text")
        return {
            "album": result.get("album", {}).get("#text"),
            "artist": result.get("artist", {}).get("#text"),
            "cover": result.get("image", [{}])[-1].get("#text"),
            "last_played_utc": {
                "unix_timestamp": last_played_uts,
                "datetime": last_played_dt,
            },
            "scrobbling_now": False,
            "title": result.get("name"),
            "url": result.get("url"),
        }
