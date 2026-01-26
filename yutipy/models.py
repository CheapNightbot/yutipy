from dataclasses import asdict, dataclass
from json import dumps
from typing import Optional, List

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
    genres: Optional[List[str]] = None
    id: Optional[int] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    role: Optional[str] = None
    url: Optional[str] = None

    # Metadata about the music platform/service
    service_name: Optional[str] = None
    service_url: Optional[str] = None


@dataclass
class Album(BaseModel):
    artists: Optional[List["Artist"]] = None
    cover: Optional[str] = None
    duration: Optional[int] = None
    explicit: Optional[bool] = None
    genres: Optional[List[str]] = None
    id: Optional[int] = None
    label: Optional[str] = None
    release_date: Optional[str] = None
    title: Optional[str] = None
    total_tracks: Optional[int] = None
    tracks: Optional[List["Track"]] = None
    type: Optional[str] = None
    upc: Optional[str] = None
    url: Optional[str] = None

    # Metadata about the music platform/service
    service_name: Optional[str] = None
    service_url: Optional[str] = None


@dataclass
class Track(BaseModel):
    album: Optional["Album"] = None
    artists: Optional[List["Artist"]] = None
    bpm: Optional[float] = None
    duration: Optional[int] = None
    explicit: Optional[bool] = None
    genre: Optional[str] = None
    gain: Optional[float] = None
    id: Optional[int] = None
    isrc: Optional[str] = None
    preview_url: Optional[str] = None
    release_date: Optional[str] = None
    title: Optional[str] = None
    track_number: Optional[int] = None
    url: Optional[str] = None

    # Metadata about the music platform/service
    service_name: Optional[str] = None
    service_url: Optional[str] = None


@dataclass
class CurrentlyPlaying(Track):
    timestamp: Optional[int] = None
    progress: Optional[int] = None
    is_playing: Optional[bool] = None
    currently_playing_type: Optional[str] = None

    # Metadata about the music platform/service
    service_name: Optional[str] = None
    service_url: Optional[str] = None
