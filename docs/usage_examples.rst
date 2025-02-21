=====
Usage
=====

Here's a quick example of how to use the `yutipy` package to search for a song:

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

Spotify
-------

To use the Spotify API, you need to set the `CLIENT_ID` and `CLIENT_SECRET` for Spotify. You can do this by creating a `.env` file in the root directory of your project with the following content:

.. code-block:: text

    CLIENT_ID=your_spotify_client_id
    CLIENT_SECRET=your_spotify_client_secret

Alternatively, you can manually provide these values when creating an object of the `Spotipy` class:

.. code-block:: python

    from yutipy.spotify import Spotipy

    spotify = Spotipy(client_id="your_spotify_client_id", client_secret="your_spotify_client_secret")

.. code-block:: python

    from yutipy.spotify import Spotipy

    with Spotipy() as spotify:
        result = spotify.search("Artist Name", "Song Title")
        print(result)

OR, if you have the ISRC or UPC of the song, you can use the `search_advanced` method:

.. code-block:: python

    from yutipy.spotify import Spotipy

    spotify = Spotipy()
    # ISRC for "single" tracks & UPC for "album" tracks. Only one of them is required.
    result = spotify.search_advanced("Artist Name", "Song Title", isrc="USAT29900609", upc="00602517078194")

YouTube Music
-------------

.. code-block:: python

    from yutipy.musicyt import MusicYT

    music_yt = MusicYT()
    result = music_yt.search("Artist Name", "Song Title")
    print(result)
