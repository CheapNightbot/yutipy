<p align="center">
<img src="docs\_static\yutipy_header.png" alt="yutipy" />
</p>

A _**simple**_ Python package for searching and retrieving music information from various music platforms APIs, including Deezer, iTunes, Spotify, and YouTube Music.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage Example](#usage-example)
- [Contributing](#contributing)
- [License](#license)

## Features

- Simple & Easy integration with popular music APIs.
- Search for music by artist and song title across multiple platforms.
- Retrieve detailed music information, including album art, release dates, ISRC, and UPC codes.

## Installation

You can install the package using pip. Make sure you have Python 3.8 or higher installed.

```bash
pip install -U yutipy
```

## Usage Example

Here's a quick example of how to use the `yutipy` package to search for a song:

### Deezer

```python
from yutipy.deezer import Deezer

with Deezer() as deezer:
    result = deezer.search("Artist Name", "Song Title")
    print(result)
```

For more usage examples, see the [docs](#).

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Optionally, create an issue to discuss the changes you plan to make.
3. Create a new branch linked to that issue.
4. Make your changes in the new branch.
5. Write tests if you add new functionality.
6. Ensure all tests pass before opening a pull request.
7. Open a pull request for review.

Thank you for your contributions!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
