from dataclasses import dataclass
from typing import Optional


@dataclass
class MusicInfo:
    """
    A data class to store music information.

    Attributes
    ----------
    album_art : Optional[str]
        URL to the album art.
    album_title : Optional[str]
        Title of the album.
    album_type : Optional[str]
        Type of the album (e.g., album, single).
    artists : str
        Name(s) of the artist(s).
    genre : Optional[str]
        Genre of the music.
    id : str
        Unique identifier for the music.
    isrc : Optional[str]
        International Standard Recording Code.
    lyrics : Optional[str]
        Lyrics of the song.
    release_date : Optional[str]
        Release date of the music.
    tempo : Optional[float]
        Tempo of the music in BPM.
    title : str
        Title of the music.
    type : Optional[str]
        Type of the music (e.g., track, album).
    upc : Optional[str]
        Universal Product Code.
    url : str
        URL to the music on the platform.
    """

    album_art: Optional[str]
    album_title: Optional[str]
    album_type: Optional[str]
    artists: str
    genre: Optional[str]
    id: str
    isrc: Optional[str]
    lyrics: Optional[str]
    release_date: Optional[str]
    tempo: Optional[float]
    title: str
    type: Optional[str]
    upc: Optional[str]
    url: str
