def are_strings_similar(str1: str, str2: str, threshold: int = 80) -> bool:
    """
    Determine if two strings are similar based on a given threshold.

    Args:
        str1 (str): First string to compare.
        str2 (str): Second string to compare.
        threshold (int, optional): Similarity threshold. Defaults to 80.

    Returns:
        bool: True if the strings are similar, otherwise False.
    """
    from rapidfuzz import fuzz
    from rapidfuzz.utils import default_process

    similarity_score = fuzz.WRatio(str1, str2, processor=default_process)
    return similarity_score > threshold


def separate_artists(artists: str, custom_separator: str = None) -> list[str]:
    """
    Separate artist names of a song or album into a list.

    Args:
        artists (str): Artists string (e.g., artistA & artistB, artistA ft. artistB).
        custom_separator (str, optional): A specific separator to use. Defaults to None.

    Returns:
        list[str]: List of individual artists.
    """
    default_separators = [";", "/", "ft.", "ft", "feat", "feat.", "with", "&", "and"]

    if custom_separator:
        separators = [custom_separator]
    else:
        separators = default_separators

    for sep in separators:
        artists = artists.replace(sep, ",")

    return [artist.strip() for artist in artists.split(",") if artist.strip()]


def is_valid_string(string: str) -> bool:
    """Validate if a string is non-empty, alphanumeric, or contains non-whitespace characters."""
    return bool(string and (string.isalnum() or not string.isspace()))


if __name__ == "__main__":
    separate_artists("Artist A ft. Artist B")
