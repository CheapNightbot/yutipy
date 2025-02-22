=============
API Reference
=============

Main Classes
=============

The following classes are available for use, utilizing the APIs of their respective music streaming platforms:

- ``Deezer``: https://www.deezer.com
- ``iTunes``: https://music.apple.com
- ``Spotify``: https://spotify.com
- ``YouTube Music``: https://music.youtube.com

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

Spotify
-------

.. autoclass:: yutipy.spotify.Spotify
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: is_session_closed

YouTube Music
-------------

.. autoclass:: yutipy.musicyt.MusicYT
    :members:
    :inherited-members:
    :noindex:

Data Classes
=============

MusicInfo
---------

.. autoclass:: yutipy.models.MusicInfo
    :members:
    :noindex:
    :exclude-members: album_art, album_title, album_type, artists, genre, id, isrc, lyrics, release_date, tempo, title, type, upc, url

Exceptions
=============

.. autoclass:: yutipy.exceptions.YutipyException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.InvalidValueException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.DeezerException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.ItunesException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.SpotifyException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.MusicYTException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.AuthenticationException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.NetworkException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback

.. autoclass:: yutipy.exceptions.InvalidResponseException
    :members:
    :inherited-members:
    :noindex:
    :exclude-members: add_note, args, with_traceback
