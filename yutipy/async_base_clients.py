"""Async base classes for services."""

__all__ = ["AsyncBaseService", "AsyncBaseClient"]

import base64
import secrets
from time import time
from urllib.parse import urlencode

import httpx

from yutipy.exceptions import AuthenticationException, InvalidValueException
from yutipy.logger import logger


class AsyncBaseService:
    """Base class for async services that do not require authentication."""

    def __init__(
        self,
        service_name: str,
        service_url: str,
        api_url: str,
    ) -> None:
        """Initializes the service.

        Parameters
        ----------
        service_name : str
            The service name class belongs to.
        service_url : str
            The service URL for the music service.
        api_url : str
            The base API URL for the service.
        """
        self.service_name = service_name
        self.service_url = service_url
        self._api_url = api_url
        self._session: httpx.AsyncClient | None = None
        self._is_session_closed = False

    async def __aenter__(self):
        """Enters the async context."""
        self._session = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Exits the async context."""
        await self.close_session()

    async def close_session(self) -> None:
        """Closes the current session."""
        if not self.is_session_closed:
            if self._session:
                await self._session.aclose()
            self._is_session_closed = True

    @property
    def is_session_closed(self) -> bool:
        """Checks if the session is closed."""
        return self._is_session_closed


class AsyncBaseClient(AsyncBaseService):
    """Base class for async services with Client Credentials grant type."""

    def __init__(
        self,
        service_name: str,
        service_url: str,
        api_url: str,
        access_token_url: str,
        client_id: str = "",
        client_secret: str = "",
        defer_load: bool = False,
    ) -> None:
        """Initializes async client."""
        super().__init__(
            service_name=service_name,
            service_url=service_url,
            api_url=api_url,
        )

        self._access_token = ""
        self._access_token_url = access_token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._defer_load = defer_load
        self._token_expires_in = 0.0
        self._token_requested_at = 0.0

        if not defer_load:
            logger.warning(
                "Async client initialization: defer_load should typically be True for async. "
                "Call `await load_token_after_init()` manually."
            )

    async def load_token_after_init(self) -> None:
        """Explicitly load the access token after initialization."""
        token_info = None
        try:
            token_info = self.load_access_token()
            if token_info and not isinstance(token_info, dict):
                raise InvalidValueException("`load_access_token()` should return a dict.")
        except NotImplementedError:
            logger.warning(
                "`load_access_token` is not implemented. Falling back to requesting new access token."
            )
        finally:
            if not token_info or not token_info.get("access_token"):
                token_info = await self._get_access_token()
            self._access_token = token_info.get("access_token")
            self._token_expires_in = token_info.get("expires_in")
            self._token_requested_at = token_info.get("requested_at")

            try:
                self.save_access_token(token_info)
            except NotImplementedError:
                logger.warning("`save_access_token` is not implemented.")

    def _authorization_header(self) -> dict:
        """Generates the authorization header."""
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _get_access_token(self) -> dict:
        """Gets the API access token asynchronously."""
        auth_string = f"{self._client_id}:{self._client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        url = self._access_token_url
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        try:
            logger.info(f"Authenticating with {self.service_name} API (async).")
            assert self._session is not None
            response = await self._session.post(
                url=url, headers=headers, data=data, timeout=30
            )
            logger.debug(f"Authentication response status code: {response.status_code}")
            response.raise_for_status()
        except httpx.RequestError as e:
            raise AuthenticationException(
                f"Something went wrong authenticating with {self.service_name}: {e}"
            )

        response_json = response.json()
        response_json["requested_at"] = time()
        return response_json

    async def _refresh_access_token(self) -> None:
        """Refreshes the token if it has expired."""
        try:
            if time() - self._token_requested_at >= self._token_expires_in:
                token_info = await self._get_access_token()

                try:
                    self.save_access_token(token_info)
                except NotImplementedError:
                    logger.warning("Token saving not implemented.")

                self._access_token = token_info.get("access_token")
                self._token_expires_in = token_info.get("expires_in")
                self._token_requested_at = token_info.get("requested_at")
            else:
                logger.debug("The access token is still valid.")
        except TypeError:
            logger.info("Something went wrong refreshing the access token.")

    def save_access_token(self, token_info: dict) -> None:
        """Saves the access token (must be overridden in subclass)."""
        raise NotImplementedError(
            "The `save_access_token` method must be overridden in a subclass."
        )

    def load_access_token(self) -> dict | None:
        """Loads the access token (must be overridden in subclass)."""
        raise NotImplementedError(
            "The `load_access_token` method must be overridden in a subclass."
        )
