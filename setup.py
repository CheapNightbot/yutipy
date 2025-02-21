from setuptools import setup, find_packages

setup(
    name="yutipy",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Cheap Nightbot",
    author_email="hi@cheapnightbot.slmail.me",
    description="A simple Python package for searching and retrieving music information from various music platforms APIs, including Deezer, iTunes, Spotify, and YouTube Music.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/CheapNightbot/yutipy",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.3",
        "rapidfuzz==3.12.1",
        "ytmusicapi==1.10.1",
        "python-dotenv==1.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.4",
            "sphinx>=7.2.6",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
