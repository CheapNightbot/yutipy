__all__ = ["Itunes"]

from datetime import datetime

import requests

from yutipy.base_clients import BaseService
from yutipy.exceptions import InvalidResponseException, InvalidValueException
from yutipy.logger import logger
from yutipy.models import Album, Artist, Track
from yutipy.utils.helpers import guess_album_type, is_valid_string


class Itunes(BaseService):
    """A class to interact with the iTunes API."""

    def __init__(self) -> None:
        """"""
        super().__init__(
            service_name="iTunes",
            service_url="https://music.apple.com",
            api_url="https://itunes.apple.com",
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
        list[Track | Album] | None
            A list of Track or Album objects if found, otherwise None.

        Raises
        ------
        InvalidValueException
            If the artist or song name is invalid, or if the limit is out of range.
        InvalidResponseException
            If the API response cannot be parsed.
        """
        if not is_valid_string(artist) or not is_valid_string(song):
            raise InvalidValueException(
                "Artist and song names must be valid strings and can't be empty."
            )

        if limit < 1 or limit > 50:
            raise InvalidValueException("Limit must be between 1 and 50.")

        query = (
            f'?term="{song}" by "{artist}"&media=music&entity=song,album&limit={limit}'
        )
        query_url = f"{self._api_url}/search{query}"

        try:
            logger.info(f'Searching iTunes for `artist="{artist}"` and `song="{song}"`')
            logger.debug(f"Query URL: {query_url}")
            response = self._session.get(query_url, timeout=30)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            logger.debug("Parsing response JSON.")
            result = response.json()
        except requests.RequestException as e:
            logger.warning(f"Unexpected error while searching iTunes: {e}")
            return None
        except requests.JSONDecodeError as e:
            raise InvalidResponseException(
                f"Failed to parse JSON response from iTunes: {e}"
            )

        mapped_results: list[Track | Album] = []
        for item in result.get("results", []):
            kind = item.get("kind")
            wrapper_type = item.get("wrapperType")

            if kind == "song" and wrapper_type == "track":
                track = Track(
                    album=Album(
                        cover=item.get("artworkUrl100"),
                        explicit=item.get("collectionExplicitness") == "explicit",
                        id=item.get("collectionId"),
                        title=item.get("collectionName"),
                        total_tracks=item.get("trackCount"),
                        type=guess_album_type(item.get("trackCount", 0)),
                        url=item.get("collectionViewUrl"),
                    ),
                    artists=[
                        Artist(
                            id=item.get("artistId"),
                            name=item.get("artistName"),
                            url=item.get("artistViewUrl"),
                        )
                    ],
                    duration=(item.get("trackTimeMillis", 1000) // 1000),
                    explicit=item.get("trackExplicitness") == "explicit",
                    genre=item.get("primaryGenreName"),
                    id=item.get("trackId"),
                    preview_url=item.get("previewUrl"),
                    release_date=self._format_release_date(item.get("releaseDate", "")),
                    title=item.get("trackName"),
                    track_number=item.get("trackNumber"),
                    url=item.get("trackViewUrl"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results.append(track)

            elif wrapper_type == "collection":
                album = Album(
                    artists=[
                        Artist(
                            id=item.get("artistId"),
                            name=item.get("artistName"),
                            url=item.get("artistViewUrl"),
                        )
                    ],
                    cover=item.get("artworkUrl100"),
                    explicit=item.get("collectionExplicitness") == "explicit",
                    genres=[item.get("primaryGenreName")],
                    id=item.get("collectionId"),
                    release_date=self._format_release_date(item.get("releaseDate", "")),
                    title=item.get("collectionName"),
                    total_tracks=item.get("trackCount"),
                    type=guess_album_type(item.get("trackCount", 0)),
                    url=item.get("collectionViewUrl"),
                    service_name=self.service_name,
                    service_url=self.service_url,
                )
                mapped_results.append(album)

        return mapped_results if mapped_results else None

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
