__all__ = [
    "AuthenticationException",
    "InvalidResponseException",
    "InvalidValueException",
    "NetworkException",
    "YutipyException",
]


# Base Exception
class YutipyException(Exception):
    """Base class for exceptions in the Yutipy package."""

    pass


# Service Exceptions
class DeezerException(YutipyException):
    """Exception raised for errors related to the Deezer API."""

    pass


class ItunesException(YutipyException):
    """Exception raised for errors related to the iTunes API."""

    pass


class KKBoxException(YutipyException):
    """Exception raised for erros related to the KKBOX Open API."""

    pass


class MusicYTException(YutipyException):
    """Exception raised for errors related to the YouTube Music API."""

    pass


class SpotifyException(YutipyException):
    """Exception raised for errors related to the Spotify API."""

    pass


# Generic Exceptions
class AuthenticationException(YutipyException):
    """Exception raised for authentication errors."""

    pass


class InvalidResponseException(YutipyException):
    """Exception raised for invalid responses from APIs."""

    pass


class InvalidValueException(YutipyException):
    """Exception raised for invalid values."""

    pass


class NetworkException(YutipyException):
    """Exception raised for network-related errors."""

    pass
