=============
API Reference
=============

Main Classes
=============

Deezer
------

.. autoclass:: yutipy.deezer.Deezer
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed

iTunes
------

.. autoclass:: yutipy.itunes.Itunes
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed

KKBox
-----

.. autoclass:: yutipy.kkbox.KKBox
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed, SERVICE_NAME, ACCESS_TOKEN_URL

Lastfm
------

.. autoclass:: yutipy.lastfm.LastFm
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed

Spotify
-------

.. autoclass:: yutipy.spotify.Spotify
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed, SERVICE_NAME, ACCESS_TOKEN_URL

.. autoclass:: yutipy.spotify.SpotifyAuth
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed, SERVICE_NAME, ACCESS_TOKEN_URL, USER_AUTH_URL

YouTube Music
-------------

.. autoclass:: yutipy.musicyt.MusicYT
    :members:
    :inherited-members:
    :noindex:


Data Classes
=============

Album
-----

.. autoclass:: yutipy.models.Album
    :members:
    :noindex:

Artist
------

.. autoclass:: yutipy.models.Artist
    :members:
    :noindex:

Track
-----

.. autoclass:: yutipy.models.Track
    :members:
    :noindex:

CurrentlyPlaying
----------------

.. autoclass:: yutipy.models.CurrentlyPlaying
    :members:
    :noindex:

Exceptions
=============

Base Exception
--------------

.. autoclass:: yutipy.exceptions.YutipyException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

Generic Exceptions
------------------

.. autoclass:: yutipy.exceptions.AuthenticationException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.InvalidResponseException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.InvalidValueException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback
