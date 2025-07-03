import pytest

from yutipy.listenbrainz import ListenBrainz
from tests import BaseResponse


@pytest.fixture
def listenbrainz():
    return ListenBrainz()


class MockResponseUsers(BaseResponse):
    @staticmethod
    def json():
        return {
            "users": [
                {"user_name": "test4test"},
                {"user_name": "lb_test"},
                {"user_name": "lb-test"},
                {"user_name": "muz-test"},
                {"user_name": "tes--"},
                {"user_name": "lb_test_1"},
                {"user_name": "suvid_test"},
                {"user_name": "testins"},
                {"user_name": "hemang-test"},
                {"user_name": "Test4585"},
            ]
        }


@pytest.fixture
def mock_response_users(listenbrainz, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponseUsers()

    monkeypatch.setattr(listenbrainz._ListenBrainz__session, "get", mock_get)


def test_find_user(listenbrainz, mock_response_users):
    username = "Test4585"
    user_name = listenbrainz.find_user(username=username)
    assert user_name is not None
    assert username == user_name

    username = "potato"
    user_name = listenbrainz.find_user(username=username)
    assert user_name is None


def test_find_user_case_insensitive(listenbrainz, mock_response_users):
    username = "muz-TEST"
    user_name = listenbrainz.find_user(username=username)
    assert user_name is not None
    assert username.lower() == user_name.lower()
