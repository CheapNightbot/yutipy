==============
Usage Examples
==============

Here's a quick example of how to use the **yutipy** package to search for a song:

.. important::
    All examples here—except for the `YouTube Music`_—use the ``with`` context manager to initialize an instance of the respective class,
    as those classes internally use ``requests.Session()`` for making requests to APIs.
    This approach ensures that the session is automatically closed once you exit the context. Although using ``with`` is not mandatory,
    if you instantiate an object without it, you are responsible for closing the session after use by calling the ``close_session()`` method on that object.

Deezer
------

.. code-block:: python

    from yutipy.deezer import Deezer

    with Deezer() as deezer:
        result = deezer.search("Artist Name", "Song Title")
        print(result)

iTunes
------

.. code-block:: python

    from yutipy.itunes import Itunes

    with Itunes() as itunes:
        result = itunes.search("Artist Name", "Song Title")
        print(result)


KKBOX
-------

To use the KKBOX Open API, you need to set the ``KKBOX_CLIENT_ID`` and ``KKBOX_CLIENT_SECRET`` for KKBOX. You can do this by creating a ``.env`` file in the root directory of your project with the following content:

.. admonition:: .env

    .. code-block:: bash

        KKBOX_CLIENT_ID=<your_kkbox_client_id>
        KKBOX_CLIENT_SECRET=<your_kkbox_client_secret>

Alternatively, you can manually provide these values when creating an object of the `KKBox` class:

.. code-block:: python

    from yutipy.kkbox import KKBox

    kkbox = KKBox(client_id="your_kkbox_client_id", client_secret="your_kkbox_client_secret")

.. code-block:: python

    from yutipy.kkbox import KKBox

    with KKBox() as kkbox:
        result = kkbox.search("Artist Name", "Song Title")
        print(result)

Spotify
-------

To use the Spotify API, you need to set the ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` for Spotify. You can do this by creating a ``.env`` file in the root directory of your project with the following content:

.. admonition:: .env

    .. code-block:: bash

        SPOTIFY_CLIENT_ID=<your_spotify_client_id>
        SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>

Alternatively, you can manually provide these values when creating an object of the `Spotify` class:

.. code-block:: python

    from yutipy.spotify import Spotify

    spotify = Spotify(client_id="your_spotify_client_id", client_secret="your_spotify_client_secret")

.. code-block:: python

    from yutipy.spotify import Spotify

    with Spotify() as spotify:
        result = spotify.search("Artist Name", "Song Title")
        print(result)

OR, if you have the ":abbr:`ISRC (International Standard Recording Code)`" or ":abbr:`UPC (Universal Product Code)`" of the song, you can use the `search_advanced` method:

.. code-block:: python

    from yutipy.spotify import Spotify

    with Spotify() as spotify:
        # ISRC for "single" tracks & UPC for "album" tracks. Only one of them is required.
        result = spotify.search_advanced("Artist Name", "Song Title", isrc="USAT29900609", upc="00602517078194")
        print(result)

YouTube Music
-------------

.. code-block:: python

    from yutipy.musicyt import MusicYT

    music_yt = MusicYT()
    result = music_yt.search("Artist Name", "Song Title")
    print(result)

Yutipy Music
------------

.. code-block:: python

    from yutipy.yutify_music import YutipyMusic

    with YutipyMusic() as yutipy_music:
        result = yutify_music.search("Artist Name", "Song Title")
        print(result)
