import pytest
from pytest import raises

from yutipy.exceptions import KKBoxException, InvalidValueException
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


def test_get_html_widget(kkbox):
    html_widget = kkbox.get_html_widget(id="8rceGrek59bDS0HmQH", content_type="song")
    assert html_widget is not None
    assert isinstance(html_widget, str)

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="8rceGrek59bDS0HmQH", content_type="track")

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="8rceGrek59bDS0HmQH", content_type="song", territory="US")

    with raises(InvalidValueException):
        kkbox.get_html_widget(id="8rceGrek59bDS0HmQH", content_type="song", widget_lang="JP")


def test_close_session(kkbox):
    kkbox.close_session()
    assert kkbox.is_session_closed
