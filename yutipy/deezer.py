from pprint import pprint
from typing import Dict, List, Optional

import requests

from yutipy.exceptions import (
    DeezerException,
    InvalidResponseException,
    InvalidValueException,
    NetworkException,
)
from yutipy.models import MusicInfo
from yutipy.utils.cheap_utils import are_strings_similar, is_valid_string


class Deezer:
    """A class to interact with the Deezer API."""

    def __init__(self) -> None:
        """Initializes the Deezer class and sets up the session."""
        self._session = requests.Session()
        self.api_url = "https://api.deezer.com"
        self._is_session_closed = False

    def __enter__(self) -> "Deezer":
        """Enters the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Exits the runtime context related to this object."""
        self._close_session()

    def close_session(self) -> None:
        """Closes the current session."""
        if not self.is_session_closed:
            self._session.close()
            self._is_session_closed = True

    @property
    def is_session_closed(self) -> bool:
        """Checks if the session is closed."""
        return self._is_session_closed

    def search(self, artist: str, song: str) -> Optional[MusicInfo]:
        """
        Searches for a song by artist and title.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.

        Returns
        -------
        Optional[MusicInfo_]
            The music information if found, otherwise None.
        """
        if not is_valid_string(artist) or not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        search_types = ["track", "album"]

        for search_type in search_types:
            endpoint = f"{self.api_url}/search/{search_type}"
            query = f'?q=artist:"{artist}" {search_type}:"{song}"&limit=10'
            query_url = endpoint + query

            try:
                response = self._session.get(query_url, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                raise NetworkException(f"Network error occurred: {e}")
            except Exception as e:
                raise DeezerException(f"An error occurred while searching Deezer: {e}")

            try:
                result = response.json()["data"]
            except (IndexError, KeyError, ValueError) as e:
                raise InvalidResponseException(f"Invalid response received: {e}")

            music_info = self._parse_results(artist, song, result)
            if music_info:
                return music_info

        return None

    def _get_upc_isrc(self, music_id: int, music_type: str) -> Optional[Dict]:
        """
        Retrieves UPC and ISRC information for a given music ID and type.

        Parameters
        ----------
        music_id : int
            The ID of the music.
        music_type : str
            The type of the music (track or album).

        Returns
        -------
        Optional[Dict]
            A dictionary containing UPC and ISRC information.
        """
        if music_type == "track":
            return self._get_track_info(music_id)
        elif music_type == "album":
            return self._get_album_info(music_id)
        else:
            raise DeezerException(f"Invalid music type: {music_type}")

    def _get_track_info(self, music_id: int) -> Optional[Dict]:
        """
        Retrieves track information for a given track ID.

        Parameters
        ----------
        music_id : int
            The ID of the track.

        Returns
        -------
        Optional[Dict]
            A dictionary containing track information.
        """
        query_url = f"{self.api_url}/track/{music_id}"
        try:
            response = self._session.get(query_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")
        except Exception as e:
            raise DeezerException(f"An error occurred while fetching track info: {e}")

        try:
            result = response.json()
        except ValueError as e:
            raise InvalidResponseException(f"Invalid response received: {e}")

        return {
            "isrc": result.get("isrc"),
            "release_date": result.get("release_date"),
            "tempo": result.get("bpm"),
        }

    def _get_album_info(self, music_id: int) -> Optional[Dict]:
        """
        Retrieves album information for a given album ID.

        Parameters
        ----------
        music_id : int
            The ID of the album.

        Returns
        -------
        Optional[Dict]
            A dictionary containing album information.
        """
        query_url = f"{self.api_url}/album/{music_id}"
        try:
            response = self._session.get(query_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkException(f"Network error occurred: {e}")
        except Exception as e:
            raise DeezerException(f"An error occurred while fetching album info: {e}")

        try:
            result = response.json()
        except ValueError as e:
            raise InvalidResponseException(f"Invalid response received: {e}")

        return {
            "genre": (
                result["genres"]["data"][0]["name"]
                if result["genres"]["data"]
                else None
            ),
            "release_date": result.get("release_date"),
            "upc": result.get("upc"),
        }

    def _parse_results(
        self, artist: str, song: str, results: List[Dict]
    ) -> Optional[MusicInfo]:
        """
        Parses the search results to find a matching song.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        results : List[Dict]
            The search results from the API.

        Returns
        -------
        Optional[MusicInfo]
            The music information if a match is found, otherwise None.
        """
        for result in results:
            if not (
                are_strings_similar(result["title"], song)
                and are_strings_similar(result["artist"]["name"], artist)
            ):
                continue

            return self._extract_music_info(result)

        return None

    def _extract_music_info(self, result: Dict) -> MusicInfo:
        """
        Extracts music information from a search result.

        Parameters
        ----------
        result : Dict
            A single search result from the API.

        Returns
        -------
        MusicInfo
            The extracted music information.
        """
        music_type = result["type"]
        music_info = MusicInfo(
            album_art=(
                result["album"]["cover_xl"]
                if music_type == "track"
                else result["cover_xl"]
            ),
            album_title=(
                result["album"]["title"] if music_type == "track" else result["title"]
            ),
            album_type=result.get("record_type", music_type),
            artists=result["artist"]["name"],
            genre=None,
            id=result["id"],
            isrc=None,
            lyrics=None,
            release_date=None,
            tempo=None,
            title=result["title"],
            type=music_type,
            upc=None,
            url=result["link"],
        )

        if music_type == "track":
            track_info = self._get_upc_isrc(result["id"], music_type)
            music_info.isrc = track_info.get("isrc")
            music_info.release_date = track_info.get("release_date")
            music_info.tempo = track_info.get("tempo")
        else:
            album_info = self._get_upc_isrc(result["id"], music_type)
            music_info.upc = album_info.get("upc")
            music_info.release_date = album_info.get("release_date")
            music_info.genre = album_info.get("genre")

        return music_info


if __name__ == "__main__":
    deezer = Deezer()
    try:
        artist_name = input("Artist Name: ")
        song_name = input("Song Name: ")
        pprint(deezer.search(artist_name, song_name))
    finally:
        deezer._close_session()
