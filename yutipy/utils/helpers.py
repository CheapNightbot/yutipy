def is_valid_string(string: str) -> bool:
    """Validate if a string is non-empty, alphanumeric, or contains non-whitespace characters."""
    return bool(string and (string.isalnum() or not string.isspace()))


def guess_album_type(total_tracks: int):
    """Just guessing the album type (i.e. single, ep or album) by total track counts."""
    if total_tracks == 1:
        return "single"
    if 3 <= total_tracks <= 5:
        return "ep"
    if total_tracks >= 7:
        return "album"
    return "unknown"
