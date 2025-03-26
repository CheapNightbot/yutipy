from datetime import datetime
from pprint import pprint
from typing import Optional, Dict

import requests

from yutipy.exceptions import (
    InvalidResponseException,
    InvalidValueException,
    NetworkException,
    ItunesException,
)
from yutipy.models import MusicInfo
from yutipy.utils.cheap_utils import are_strings_similar, is_valid_string


class Itunes:
    """A class to interact with the iTunes API."""

    def __init__(self) -> None:
        """Initializes the iTunes class and sets up the session."""
        self._session = requests.Session()
        self.api_url = "https://itunes.apple.com"
        self._is_session_closed = False
        self.normalize_non_english = True
        self._translation_session = requests.Session()

    def __enter__(self) -> "Itunes":
        """Enters the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
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

        self.normalize_non_english = normalize_non_english

        entities = ["song", "album"]
        for entity in entities:
            endpoint = f"{self.api_url}/search"
            query = f"?term={artist} - {song}&media=music&entity={entity}&limit={limit}"
            query_url = endpoint + query

            try:
                response = self._session.get(query_url, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                raise NetworkException(f"Network error occurred: {e}")
            except Exception as e:
                raise ItunesException(f"An error occurred while searching iTunes: {e}")

            try:
                result = response.json()["results"]
            except (IndexError, KeyError, ValueError) as e:
                raise InvalidResponseException(f"Invalid response received: {e}")

            music_info = self._parse_result(artist, song, result)
            if music_info:
                return music_info

        return None

    def _parse_result(
        self, artist: str, song: str, results: list[dict]
    ) -> Optional[MusicInfo]:
        """
        Parses the search results to find a matching song.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        results : list
            The search results from the API.

        Returns
        -------
        Optional[MusicInfo]
            The music information if a match is found, otherwise None.
        """
        for result in results:
            if not (
                are_strings_similar(
                    result.get("trackName", result["collectionName"]),
                    song,
                    use_translation=self.normalize_non_english,
                    translation_session=self._translation_session,
                )
                and are_strings_similar(
                    result["artistName"],
                    artist,
                    use_translation=self.normalize_non_english,
                    translation_session=self._translation_session,
                )
            ):
                continue

            album_title, album_type = self._extract_album_info(result)
            release_date = self._format_release_date(result["releaseDate"])

            return MusicInfo(
                album_art=result["artworkUrl100"],
                album_title=album_title,
                album_type=album_type.lower(),
                artists=result["artistName"],
                genre=result["primaryGenreName"],
                id=result.get("trackId", result["collectionId"]),
                isrc=None,
                lyrics=None,
                release_date=release_date,
                tempo=None,
                title=result.get("trackName", album_title),
                type=result["wrapperType"],
                upc=None,
                url=result.get("trackViewUrl", result["collectionViewUrl"]),
            )

        return None

    def _extract_album_info(self, result: dict) -> tuple:
        """
        Extracts album information from a search result.

        Parameters
        ----------
        result : dict
            A single search result from the API.

        Returns
        -------
        tuple
            The extracted album title and type.
        """
        try:
            album_title, album_type = result["collectionName"].split("-")
            return album_title.strip(), album_type.strip()
        except ValueError:
            return result["collectionName"], result["wrapperType"]

    def _format_release_date(self, release_date: str) -> str:
        """
        Formats the release date to a standard format.

        Parameters
        ----------
        release_date : str
            The release date from the API.

        Returns
        -------
        str
            The formatted release date.
        """
        return datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y-%m-%d"
        )


if __name__ == "__main__":
    itunes = Itunes()

    try:
        artist_name = input("Artist Name: ")
        song_name = input("Song Name: ")
        pprint(itunes.search(artist_name, song_name))
    finally:
        itunes.close_session()
