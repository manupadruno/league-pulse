import os
import json
from datetime import datetime, timezone
from pathlib import Path


def save_raw(data: dict, entity: str, identifier: str) -> None:
    """
    Saves raw data to a JSON file in the specified directory structure.

    Args:
        data (dict): The data to be saved.
        entity (str): The entity type (e.g., 'matches', 'competitions').
        identifier (str): A unique identifier for the data (e.g., competition code, match ID).
    """

    # Create the directory structure if it doesn't exist
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    directory = f"data/raw/{entity}"
    os.makedirs(directory, exist_ok=True)

    # Define the file path
    file_path = f"{directory}/{timestamp}_{identifier}.json"

    # Save the data to a JSON file
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print(f"Data saved to {file_path}")  # TODO: Modificar a logging


def load_raw(entity: str, identifier_prefix: str) -> dict:
    """
    Loads raw data from a JSON file based on the entity and identifier prefix.

    Args:
        entity (str): The entity type (e.g., 'matches', 'competitions').
        identifier_prefix (str): The prefix of the identifier for the data to load.

    Returns:
        dict: The loaded data.
    """
    directory = f"data/raw/{entity}"
    directory_path = Path(directory)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist.")

    # Find the latest file that matches the identifier prefix
    files = list(directory_path.glob(f"*_{identifier_prefix}*"))

    if len(files) == 0:
        raise FileNotFoundError(
            f"No files found with in folder {entity} with identifier {identifier_prefix}")

    with open(max(files), "r") as json_file:
        data = json.load(json_file)
        return data
