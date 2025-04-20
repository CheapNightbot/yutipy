import pytest

from yutipy.exceptions import SpotifyException
from yutipy.models import MusicInfo
from yutipy.spotify import Spotify, SpotifyAuth


@pytest.fixture(scope="module")
def spotify():
    try:
        return Spotify()
    except SpotifyException:
        pytest.skip("Spotify credentials not found")


@pytest.fixture(scope="module")
def spotify_auth():
    return SpotifyAuth(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost/callback",
        scopes=["user-read-email", "user-read-private"],
    )


def test_search(spotify):
    artist = "Adele"
    song = "Hello"
    result = spotify.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert result.title == song
    assert artist in result.artists


def test_search_advanced_with_isrc(spotify):
    artist = "Adele"
    song = "Hello"
    isrc = "GBBKS1500214"
    result = spotify.search_advanced(artist, song, isrc=isrc)
    assert result is not None
    assert result.isrc == isrc


def test_search_advanced_with_upc(spotify):
    artist = "Miles Davis"
    album = "Kind Of Blue (Legacy Edition)"
    upc = "888880696069"
    result = spotify.search_advanced(artist, album, upc=upc)
    print(result)
    assert result is not None


def test_get_artists_ids(spotify):
    artist = "Adele"
    artist_ids = spotify._get_artists_ids(artist)
    assert isinstance(artist_ids, list)
    assert len(artist_ids) > 0


def test_close_session(spotify):
    spotify.close_session()
    assert spotify.is_session_closed


def test_get_authorization_url(spotify_auth):
    state = spotify_auth.generate_state()
    auth_url = spotify_auth.get_authorization_url(state=state)
    assert "https://accounts.spotify.com/authorize" in auth_url
    assert "response_type=code" in auth_url
    assert f"client_id={spotify_auth.client_id}" in auth_url


def test_get_user_profile(spotify_auth, monkeypatch):
    def mock_authorization_header():
        return {"Authorization": "Bearer test_token"}

    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200

            @staticmethod
            def raise_for_status():
                pass  # Simulates a successful response with no exceptions raised

            @staticmethod
            def json():
                return {
                    "display_name": "Test User",
                    "images": [
                        {
                            "url": "https://example.com/image.jpg",
                            "height": 300,
                            "width": 300,
                        }
                    ],
                }

        return MockResponse()

    monkeypatch.setattr(
        spotify_auth, "_SpotifyAuth__authorization_header", mock_authorization_header
    )
    monkeypatch.setattr(spotify_auth._SpotifyAuth__session, "get", mock_get)

    user_profile = spotify_auth.get_user_profile()
    assert user_profile is not None
    assert user_profile["display_name"] == "Test User"
    assert len(user_profile["images"]) == 1
    assert user_profile["images"][0]["url"] == "https://example.com/image.jpg"


def test_callback_handler(spotify_auth, monkeypatch):
    def mock_get_access_token(*args, **kwargs):
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "requested_at": 1234567890,
        }

    monkeypatch.setattr(
        spotify_auth, "_SpotifyAuth__get_access_token", mock_get_access_token
    )

    spotify_auth.callback_handler("test_code", "test_state", "test_state")
    assert spotify_auth._SpotifyAuth__access_token == "test_access_token"
    assert spotify_auth._SpotifyAuth__refresh_token == "test_refresh_token"
    assert spotify_auth._SpotifyAuth__token_expires_in == 3600
    assert spotify_auth._SpotifyAuth__token_requested_at == 1234567890
