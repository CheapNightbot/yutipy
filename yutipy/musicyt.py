import os
from pprint import pprint
from typing import Optional

from ytmusicapi import YTMusic, exceptions

from yutipy.exceptions import (
    InvalidResponseException,
    InvalidValueException,
    NetworkException,
)
from yutipy.models import MusicInfo
from yutipy.utils.cheap_utils import are_strings_similar, is_valid_string


class MusicYT:
    """A class to interact with the YouTube Music API."""

    def __init__(self) -> None:
        """Initializes the YouTube Music class and sets up the session."""
        self.ytmusic = YTMusic()

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

        query = f"{artist} - {song}"

        try:
            results = self.ytmusic.search(query=query)
        except exceptions.YTMusicServerError as e:
            raise NetworkException(f"Network error occurred: {e}")

        for result in results:
            if self._is_relevant_result(artist, song, result):
                return self._process_result(result)

        return None

    def _is_relevant_result(self, artist: str, song: str, result: dict) -> bool:
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
            are_strings_similar(result.get("title"), song)
            and are_strings_similar(_artist.get("name"), artist)
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

    def _process_result(self, result: dict) -> MusicInfo:
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
            return self._get_song(result)
        else:
            return self._get_album(result)

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
        title = result["title"]
        artist_names = ", ".join([artist["name"] for artist in result["artists"]])
        video_id = result["videoId"]
        song_url = f"https://music.youtube.com/watch?v={video_id}"
        lyrics_id = self.ytmusic.get_watch_playlist(video_id)

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

        try:
            lyrics = self.ytmusic.get_lyrics(lyrics_id.get("lyrics"))
        except exceptions.YTMusicUserError:
            lyrics = {}

        album_art = result.get("thumbnails", [{}])[-1].get("url", None)

        return MusicInfo(
            album_art=album_art,
            album_title=None,
            album_type="single",
            artists=artist_names,
            genre=None,
            id=video_id,
            isrc=None,
            lyrics=lyrics.get("lyrics"),
            release_date=release_date,
            tempo=None,
            title=title,
            type="song",
            upc=None,
            url=song_url,
        )

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

        try:
            lyrics_id = self.ytmusic.get_watch_playlist(browse_id)
            lyrics = self.ytmusic.get_lyrics(lyrics_id.get("lyrics"))
        except (exceptions.YTMusicServerError, exceptions.YTMusicUserError):
            lyrics = {}

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
            lyrics=lyrics.get("lyrics"),
            release_date=release_date,
            tempo=None,
            title=title,
            type="album",
            upc=None,
            url=album_url,
        )


if __name__ == "__main__":
    music_yt = MusicYT()

    artist_name = input("Artist Name: ")
    song_name = input("Song Name: ")

    pprint(music_yt.search(artist_name, song_name))
