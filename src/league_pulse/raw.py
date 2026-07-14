import os
import json
from datetime import datetime, timezone


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
