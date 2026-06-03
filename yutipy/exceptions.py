__all__ = [
    "YutipyException",
    "AuthenticationException",
    "InvalidValueException",
]


# Base Exception
class YutipyException(Exception):
    """Base class for exceptions in the yutipy package."""


# Generic Exceptions
class AuthenticationException(YutipyException):
    """
    Exception raised for authentication related errors.

    This exception should be used when authentication fails, such as when
    invalid credentials are provided or required authentication tokens are missing.

    Attributes:
        message (str): Explanation of the authentication error.
    """

class InvalidValueException(YutipyException):
    """
    Exception raised for invalid values to the function arguments.

    This exception should be used when a function receives an argument with a value
    that is not acceptable or outside the expected range.

    Attributes:
        message (str): Explanation of the error.
    """

    """Exception raised for invalid values to the function arguments."""
