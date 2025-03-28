import os
import webbrowser
from dotenv import load_dotenv, set_key


def run_config_wizard():
    """Interactive configuration wizard for setting up API keys."""
    print("Welcome to the yutipy Configuration Wizard!")
    print("This wizard will help you set up your API keys for various services.\n")

    # Load existing .env file if it exists
    env_file = ".env"
    load_dotenv(env_file)

    # List of required environment variables and their instructions
    required_vars = {
        "SPOTIFY_CLIENT_ID": {
            "description": "Spotify Client ID",
            "url": "https://developer.spotify.com/dashboard",
            "instructions": """
1. Go to your Spotify Developer Dashboard: https://developer.spotify.com/dashboard
2. Create a new app and fill in the required details.
3. Copy the "Client ID" and "Client Secret" from the app's settings.
4. Paste them here when prompted.
            """,
        },
        "SPOTIFY_CLIENT_SECRET": {
            "description": "Spotify Client Secret",
            "url": "https://developer.spotify.com/dashboard",
            "instructions": "See the steps above for Spotify Client ID.",
        },
        "KKBOX_CLIENT_ID": {
            "description": "KKBox Client ID",
            "url": "https://developer.kkbox.com/",
            "instructions": """
1. Go to the KKBOX Developer Portal: https://developer.kkbox.com/
2. Log in and create a new application.
3. Copy the "Client ID" and "Client Secret" from the app's settings.
4. Paste them here when prompted.
            """,
        },
        "KKBOX_CLIENT_SECRET": {
            "description": "KKBox Client Secret",
            "url": "https://developer.kkbox.com/",
            "instructions": "See the steps above for KKBox Client ID.",
        },
    }

    # Track whether the browser has already been opened for a service
    browser_opened = set()

    # Prompt the user for each variable
    for var, details in required_vars.items():
        current_value = os.getenv(var)
        if current_value:
            print(f"{details['description']} is already set.")
            continue

        print(f"\n{details['description']} is missing.")
        print(details["instructions"])

        # Check if the browser has already been opened for this service
        if details["url"] not in browser_opened:
            open_browser = (
                input(
                    f"Do you want to open the website to get your {details['description']}? (y/N): "
                )
                .strip()
                .lower()
            )
            if open_browser == "y":
                webbrowser.open(details["url"])
                print(f"The website has been opened in your browser: {details['url']}")
                browser_opened.add(details["url"])  # Mark this URL as opened

        # Prompt the user to enter the value
        new_value = input(f"Enter your {details['description']}: ").strip()
        if new_value:
            set_key(env_file, var, new_value)
            print(f"{details['description']} has been saved to the .env file.")

    print("\nConfiguration complete! Your API keys have been saved to the .env file.")


if __name__ == "__main__":
    run_config_wizard()
