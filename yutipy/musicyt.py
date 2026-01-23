__all__ = ["MusicYT", "MusicYTException"]

from pprint import pprint
from typing import Optional

from ytmusicapi import YTMusic, exceptions

from yutipy.base_clients import BaseService
from yutipy.exceptions import (
    InvalidResponseException,
    InvalidValueException,
    MusicYTException,
)
from yutipy.logger import logger
from yutipy.models import MusicInfo
from yutipy.utils.helpers import are_strings_similar, is_valid_string


class MusicYT(BaseService):
    """A class to interact with the YouTube Music API."""

    def __init__(self) -> None:
        self.ytmusic = YTMusic()
        super().__init__(
            service_name="YouTube Music",
            api_url="",
            session=False,
            translation_session=True,
        )

    def search(
        self,
        artist: str,
        song: str,
        limit: int = 10,
        normalize_non_english: bool = False,
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

        query = f"{artist} - {song}"
        try:
            logger.info(
                f"Searching YouTube Music for `artist='{artist}'` and `song='{song}'`"
            )
            results = self.ytmusic.search(query=query, limit=limit)
        except exceptions.YTMusicServerError as e:
            logger.warning(f"Something went wrong while searching YTMusic: {e}")
            return None

        for result in results:
            if self._is_relevant_result(
                artist,
                song,
                normalize_non_english,
                result,
            ):
                return self._process_result(result)

        logger.warning(
            f"No matching results found for artist='{artist}' and song='{song}'"
        )
        return None

    def _is_relevant_result(
        self,
        artist: str,
        song: str,
        normalize_non_english: bool,
        result: dict,
    ) -> bool:
        """
        Determine if a search result is relevant.

        Parameters
        ----------
        artist : str
            The name of the artist.
        song : str
            The title of the song.
        result : dict
            The search result from the API.

        Returns
        -------
        bool
            Whether the result is relevant.
        """
        if self._skip_categories(result):
            return False

        return any(
            are_strings_similar(
                result.get("title"),
                song,
                use_translation=normalize_non_english,
                translation_session=self._translation_session,
            )
            and are_strings_similar(
                _artist.get("name"),
                artist,
                use_translation=normalize_non_english,
                translation_session=self._translation_session,
            )
            for _artist in result.get("artists", [])
        )

    def _skip_categories(self, result: dict) -> bool:
        """
        Skip certain categories in search results.

        Parameters
        ----------
        result : dict
            The search result from the API.

        Returns
        -------
        bool
            Return `True` if the result should be skipped, else `False`.
        """
        categories_skip = [
            "artists",
            "community playlists",
            "featured playlists",
            "podcasts",
            "profiles",
            "uploads",
            "episode",
            "episodes",
        ]

        return (
            result.get("category", "").lower() in categories_skip
            or result.get("resultType", "").lower() in categories_skip
        )

    def _process_result(self, result: dict) -> Optional[MusicInfo]:
        """
        Process the search result and return relevant information as `MusicInfo`.

        Parameters
        ----------
        result : dict
            The search result from the API.

        Returns
        -------
        MusicInfo
            The extracted music information.
        """
        if result["resultType"] in ["song", "video"]:
            try:
                return self._get_song(result)
            except InvalidResponseException:
                return None
        else:
            try:
                return self._get_album(result)
            except InvalidResponseException:
                return None

    def _get_song(self, result: dict) -> MusicInfo:
        """
        Return song info as a `MusicInfo` object.

        Parameters
        ----------
        result : dict
            The search result from the API.

        Returns
        -------
        MusicInfo
            The extracted music information.
        """
        title = result.get("title")
        artist_names = ", ".join(
            [artist.get("name") for artist in result.get("artists", [])]
        )
        video_id = result.get("videoId")
        song_url = f"https://music.youtube.com/watch?v={video_id}"

        try:
            song_data = self.ytmusic.get_song(video_id)
            release_date = (
                song_data.get("microformat", {})
                .get("microformatDataRenderer", {})
                .get("uploadDate", "")
                .split("T")[0]
            )
        except (exceptions.YTMusicServerError, exceptions.YTMusicError) as e:
            raise InvalidResponseException(f"Invalid response received: {e}")

        album_art = result.get("thumbnails", [{}])[-1].get("url", None)

        music_info = MusicInfo(
            album_art=album_art,
            album_title=None,
            album_type="single",
            artists=artist_names,
            genre=None,
            id=video_id,
            isrc=None,
            release_date=release_date,
            tempo=None,
            title=title,
            type="song",
            upc=None,
            url=song_url,
        )

        return music_info

    def _get_album(self, result: dict) -> MusicInfo:
        """
        Return album info as a `MusicInfo` object.

        Parameters
        ----------
        result : dict
            The search result from the API.

        Returns
        -------
        MusicInfo
            The extracted music information.
        """
        title = result["title"]
        artist_names = ", ".join([artist["name"] for artist in result["artists"]])
        browse_id = result["browseId"]
        album_url = f"https://music.youtube.com/browse/{browse_id}"

        try:
            album_data = self.ytmusic.get_album(browse_id)
            release_date = album_data["year"]
        except (exceptions.YTMusicServerError, exceptions.YTMusicError) as e:
            raise InvalidResponseException(f"Invalid response received: {e}")

        album_art = result.get("thumbnails", [{}])[-1].get(
            "url", album_data.get("thumbnails", [{}])[-1].get("url", None)
        )

        return MusicInfo(
            album_art=album_art,
            album_title=title,
            album_type="Album",
            artists=artist_names,
            genre=None,
            id=browse_id,
            isrc=None,
            release_date=release_date,
            tempo=None,
            title=title,
            type="album",
            upc=None,
            url=album_url,
        )


if __name__ == "__main__":
    import logging

    from yutipy.logger import enable_logging

    enable_logging(level=logging.DEBUG)
    music_yt = MusicYT()
    try:
        artist_name = input("Artist Name: ")
        song_name = input("Song Name: ")
        pprint(music_yt.search(artist_name, song_name))
    finally:
        music_yt.close_session()
