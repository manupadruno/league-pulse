from requests import HTTPError

from extract import fetch_competition, fetch_matches
from raw import save_raw


def main():
    competition_codes = ["PL", "BL1"]
    seasons = [2023, 2024]

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


if __name__ == "__main__":
    main()
