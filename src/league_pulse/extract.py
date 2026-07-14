from config import API_TOKEN, BASE_URL
import requests


def fetch_competition(code: str) -> dict:
    """
    Fetches competition data from the football-data.org API.

    Args:
        code (str): The competition code (e.g., 'PL' for Premier League).

    Returns:
        dict: A dictionary containing the competition data.
    """
    url = f"{BASE_URL}/competitions/{code}"
    headers = {"X-Auth-Token": API_TOKEN}
    response = requests.get(url, headers=headers)

    response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    return response.json()


def fetch_matches(competition_code: str, season: int) -> dict:
    """
    Fetches match data for a specific competition from the football-data.org API.

    Args:
        competition_code (str): _description_
        season (int): The season for which to fetch match data.


    Returns:
        dict: _description_
    """

    url = f"{BASE_URL}/competitions/{competition_code}/matches"
    headers = {"X-Auth-Token": API_TOKEN}
    payload = {"season": season}
    response = requests.get(url, headers=headers, params=payload)

    response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    return response.json()
