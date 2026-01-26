========================
Command-Line Interface
========================

The **yutipy** package includes two CLI tools:

1. **yutipy-cli**: Search for music across multiple platforms.
2. **yutipy-config**: Configure API keys interactively.

yutipy-cli
----------

Search for music directly from the command line:

.. code-block:: bash

    yutipy-cli "Rick Astley" "Never Gonna Give You Up" --service spotify

Options:
^^^^^^^^

- **artist** (required): The name of the artist.
- **song** (required): The title of the song.
- **\-\-service** (required): Specify a single service to search (e.g., ``deezer``, ``spotify``, ``itunes``).
- **\-\-limit**: The number of results to retrieve (default: 1).
- **\-\-verbose**: Enable logging in the terminal.
- **\-\-version**: Show installed yutipy version and exit.

yutipy-config
-------------

Set up API keys interactively:

.. code-block:: bash

    yutipy-config

The wizard will guide you through obtaining and setting up API keys for supported services like KKBOX, Lastfm and Spotify.
