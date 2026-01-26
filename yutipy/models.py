from dataclasses import asdict, dataclass
from json import dumps

"""
For the service metadata fields in each model,
no need to add to each model individually.
But make sure the most outer models in the response have them.

Example:
- Track(service_name="Example Music", service_url="https://example.com", Artist(...), ...)  # no need to add in Artist model.
- Album(service_name="Example Music", service_url="https://example.com", Artist(...), Track(...), ...)  # no need to add in Artist and Track models.
"""


class BaseModel:
    def __str__(self):
        return dumps(asdict(self), indent=2, ensure_ascii=False)


@dataclass
class Artist(BaseModel):
    genres: list[str] | None = None
    id: int | None = None
    name: str | None = None
    picture: str | None = None
    role: str | None = None
    url: str | None = None

    # Metadata about the music platform/service
    service_name: str | None = None
    service_url: str | None = None


@dataclass
class Track(BaseModel):
    album: Album | None = None
    artists: list[Artist] | None = None
    bpm: float | None = None
    duration: int | None = None
    explicit: bool | None = None
    genre: str | None = None
    gain: float | None = None
    id: int | None = None
    isrc: str | None = None
    preview_url: str | None = None
    release_date: str | None = None
    title: str | None = None
    track_number: int | None = None
    url: str | None = None

    # Metadata about the music platform/service
    service_name: str | None = None
    service_url: str | None = None


@dataclass
class Album(BaseModel):
    artists: list[Artist] | None = None
    cover: str | None = None
    duration: int | None = None
    explicit: bool | None = None
    genres: list[str] | None = None
    id: int | None = None
    label: str | None = None
    release_date: str | None = None
    title: str | None = None
    total_tracks: int | None = None
    tracks: list[Track] | None = None
    type: str | None = None
    upc: str | None = None
    url: str | None = None

    # Metadata about the music platform/service
    service_name: str | None = None
    service_url: str | None = None


@dataclass
class CurrentlyPlaying(Track):
    timestamp: int | None = None
    progress: int | None = None
    is_playing: bool | None = None
    currently_playing_type: str | None = None

    # Metadata about the music platform/service
    service_name: str | None = None
    service_url: str | None = None
