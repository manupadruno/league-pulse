from requests import HTTPError
from extract import fetch_competition, fetch_matches
from transform import load_and_parse_matches
from raw import save_raw
from settings import COMPETITION_CODES, SEASONS


def extract_phase(competition_codes, seasons):
    for code in competition_codes:
        try:
            competition_data = fetch_competition(code)
            save_raw(competition_data, "competitions", code)
        except HTTPError as http_err:
            print(
                f"Error fetching competition {code}: {http_err}")

        for season in seasons:
            try:
                match_data = fetch_matches(code, season)
                save_raw(match_data, "matches", f"{code}_{season}")
            except HTTPError as http_err:
                print(
                    f"Error fetching data for {code} in season {season}: {http_err}")


def transform_phase(competition_code, season):
    matches = load_and_parse_matches(competition_code, season)
    return matches


def load_phase(matches):
    return None


def main(competition_codes, seasons):
    extract_phase(competition_codes, seasons)

    for competition_code in competition_codes:
        for season in seasons:
            try:
                matches = transform_phase(competition_code, season)
                # load_phase(matches)
            except FileNotFoundError as e:
                print(f"File {competition_code}_{season} not found")


if __name__ == "__main__":
    main(COMPETITION_CODES, SEASONS)
