from dataclasses import dataclass


@dataclass
class Artist:
    id: int | None = None
    name: str | None = None
    picture: str | None = None
    role: str | None = None
    url: str | None = None


@dataclass
class Track:
    album: Album | None = None
    artists: list[Artist] | None = None
    bpm: float | None = None
    duration: int | None = None
    explicit: bool | None = None
    gain: float | None = None
    id: int | None = None
    isrc: str | None = None
    preview_url: str | None = None
    release_date: str | None = None
    title: str | None = None
    track_number: int | None = None
    url: str | None = None


@dataclass
class Album:
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


@dataclass
class MusicInfo:
    pass


@dataclass
class UserPlaying:
    pass
