import pytest

from yutipy.exceptions import KKBoxException
from yutipy.models import MusicInfo
from yutipy.kkbox import KKBox


@pytest.fixture(scope="module")
def kkbox():
    try:
        return KKBox()
    except KKBoxException:
        pytest.skip("KKBOX credentials not found")


def test_search(kkbox):
    artist = "Porter Robinson"
    song = "Shelter"
    result = kkbox.search(artist, song)
    assert result is not None
    assert isinstance(result, MusicInfo)
    assert result.title == song
    assert artist in result.artists


def test_close_session(kkbox):
    kkbox.close_session()
    assert kkbox.is_session_closed
