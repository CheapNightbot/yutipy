import pykakasi
import requests
from rapidfuzz import fuzz
from rapidfuzz.utils import default_process

kakasi = pykakasi.kakasi()


def translate_text(
    text: str,
    sl: str = None,
    dl: str = "en",
    session: requests.Session = None,
) -> dict:
    """
    Translate text from one language to another.

    Args:
        text (str): The text to be translated.
        sl (str, optional): The source language code (e.g., 'en' for English, 'es' for Spanish). If not provided, the API will attempt to detect the source language.
        dl (str, optional): The destination language code (default is 'en' for English).
        session (requests.Session, optional): A `requests.Session` object to use for making the API request. If not provided, a new session will be created and closed within the function.
            Providing your own session can improve performance by reusing the same session for multiple requests. Don't forget to close the session afterwards.

     Returns:
        dict: A dictionary containing the following keys:
            - 'source-text': The original text.
            - 'source-language': The detected or provided source language code.
            - 'destination-text': The translated text.
            - 'destination-language': The destination language code.
    """
    default_session = False
    if session is None:
        default_session = True
        session = requests.Session()

    if sl:
        url = f"https://ftapi.pythonanywhere.com/translate?sl={sl}&dl={dl}&text={text}"
    else:
        url = f"https://ftapi.pythonanywhere.com/translate?dl={dl}&text={text}"

    response = session.get(url)
    response_json = response.json()
    result = {
        "source-text": response_json["source-text"],
        "source-language": response_json["source-language"],
        "destination-text": response_json["destination-text"],
        "destination-language": response_json["destination-language"],
    }

    if default_session:
        session.close()

    return result


def are_strings_similar(
    str1: str,
    str2: str,
    threshold: int = 80,
    use_translation: bool = True,
    translation_session: requests.Session = None,
) -> bool:
    """
    Determine if two strings are similar based on a given threshold.

    Args:
        str1 (str): First string to compare.
        str2 (str): Second string to compare.
        threshold (int, optional): Similarity threshold. Defaults to 80.
        use_translation (bool, optional): Use translations to compare strings. Defaults to ``True``
        translation_session (requests.Session, optional): A `requests.Session` object to use for making the API request. If not provided, a new session will be created and closed within the function.
            Providing your own session can improve performance by reusing the same session for multiple requests. Don't forget to close the session afterwards.

    Returns:
        bool: True if the strings are similar, otherwise False.
    """

    if use_translation:
        translated_str1 = (
            translate_text(str1, session=translation_session)["destination-text"]
            if translation_session
            else translate_text(str1)["destination-text"]
        )
        translated_str2 = (
            translate_text(str2, session=translation_session)["destination-text"]
            if translation_session
            else translate_text(str2)["destination-text"]
        )

        similarity_score = fuzz.WRatio(
            translated_str1, translated_str2, processor=default_process
        )
        if similarity_score > threshold:
            return True

    # Use transliterated strings for comparison
    str1 = "".join(item["hepburn"] for item in kakasi.convert(str1)) or str1
    str2 = "".join(item["hepburn"] for item in kakasi.convert(str2)) or str2

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


def guess_album_type(total_tracks: int):
    """Just guessing the album type (i.e. single, ep or album) by total track counts."""
    if total_tracks == 1:
        return "single"
    if 3 <= total_tracks <= 5:
        return "ep"
    if total_tracks >= 7:
        return "album"
