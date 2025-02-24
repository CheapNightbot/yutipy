<p align="center">
<img src="https://raw.githubusercontent.com/CheapNightbot/yutipy/main/docs/_static/yutipy_header.png" alt="yutipy" />
</p>

<p align="center">
<a href="https://github.com/CheapNightbot/yutipy/actions/workflows/tests.yml">
<img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/cheapnightbot/yutipy/pytest-unit-testing.yml?style=for-the-badge&label=Pytest">
</a>
<a href="https://pypi.org/project/yutipy/">
<img src="https://img.shields.io/pypi/v/yutipy?style=for-the-badge" alt="PyPI" />
</a>
<a href="https://yutipy.readthedocs.io/en/latest/">
<img src="https://img.shields.io/readthedocs/yutipy?style=for-the-badge" alt="Documentation Status" />
</a>
<a href="https://github.com/CheapNightbot/yutipy/blob/master/LICENSE">
<img src="https://img.shields.io/github/license/CheapNightbot/yutipy?style=for-the-badge" alt="License" />
</a>
<a href="https://github.com/CheapNightbot/yutipy/stargazers">
<img src="https://img.shields.io/github/stars/CheapNightbot/yutipy?style=for-the-badge" alt="Stars" />
</a>
<a href="https://github.com/CheapNightbot/yutipy/issues">
<img src="https://img.shields.io/github/issues/CheapNightbot/yutipy?style=for-the-badge" alt="Issues" />
</a>
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
- It uses `RapidFuzz` to compare & return the best match so that you can be sure you got what you asked for without having to worry and doing all that work by yourself.
- Retrieve detailed music information, including album art, release dates, lyrics, ISRC, and UPC codes.

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

For more usage examples, see the [Usage Examples](https://yutipy.readthedocs.io/en/latest/usage_examples.html) page in docs.

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
