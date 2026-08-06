from datetime import datetime

import psycopg
from requests import HTTPError
from extract import fetch_competition, fetch_matches, fetch_scorers, fetch_standings
from validate import report_discrepancies, validate_table
from query import get_matchday_clasifications, get_seasons
from transform import load_and_parse_matches, load_and_parse_competition, load_and_parse_players, load_and_parse_scorers, load_and_parse_seasons, load_and_parse_teams, parse_season, parse_standings
from raw import save_raw
from settings import COMPETITION_CODES, SEASONS
from load import get_connection, load_competition, load_matchday_clasification, load_matches, load_players, load_scorers, load_season, load_seasons, load_teams


def extract_phase(competition_codes: list[str], seasons: list[int]):
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
                scorers_data = fetch_scorers(code, season)
                save_raw(scorers_data, "scorers", f"{code}_{season}")
            except HTTPError as http_err:
                print(
                    f"Error fetching data for {code} in season {season}: {http_err}")


def transform_and_load_phase(connection: psycopg.Connection, competition_codes: list[str], years: list[int]):
    for competition_code in competition_codes:
        try:
            competition = load_and_parse_competition(competition_code)
            load_competition(connection, competition)

            competition_seasons = load_and_parse_seasons(
                competition_code, years)

        except FileNotFoundError as e:
            print(f"File {competition_code} not found, error {e}")
            continue

        for year in years:
            try:
                teams = load_and_parse_teams(competition_code, year)
                load_teams(connection, teams)
                season = next(
                    (s for s in competition_seasons if s.startDate.year == year), None)

                if season is None:
                    print(
                        f"No season found for {competition_code} in year {year}, skipping")
                    continue
                load_season(connection, season)
                matches = load_and_parse_matches(competition_code, year)
                load_matches(connection, matches)
                players = load_and_parse_players(competition_code, year)
                load_players(connection, players)
                scorers = load_and_parse_scorers(competition_code, year)
                load_scorers(connection, scorers)
                load_matchday_clasification(connection, season.id)

            except FileNotFoundError as e:
                print(f"File {competition_code}_{year} not found")
                continue
            except psycopg.IntegrityError as e:
                connection.rollback()
                print(
                    f"Integrity error loading data for {competition_code} in year {year}: {e}")
                continue


def validate_phase(connection: psycopg.Connection, competition_codes: list[str]):
    for competition_code in competition_codes:
        seasons = get_seasons(connection, competition_code)
        for season in seasons:
            try:
                matchday_clasifications = get_matchday_clasifications(
                    connection, season.id, season.currentMatchday)
                if len(matchday_clasifications) == 0:
                    print(
                        f"Skipped validation for {competition_code} season {season.id} because no finished matches were found")
                    continue
                raw_standings = fetch_standings(
                    competition_code, season.startDate.year, season.currentMatchday)
                standings = parse_standings(raw_standings)
                discrepancies = validate_table(
                    standings, matchday_clasifications)
                report_discrepancies(discrepancies)
                print(
                    f"Validated {competition_code} season {season.id} matchday {season.currentMatchday}: {len(discrepancies)} discrepancies found")

            except HTTPError as http_err:
                print(
                    f"Error fetching competition {competition_code}: {http_err}")
                continue
            except psycopg.Error as e:
                print(
                    f"Database error validating data for {competition_code} season {season.id}: {e}")
                continue


def main(competition_codes: list[str], seasons: list[int]):
    conn = get_connection()
    try:
        extract_phase(competition_codes, seasons)
        transform_and_load_phase(conn, competition_codes, seasons)
        validate_phase(conn, competition_codes)
    finally:
        conn.close()


if __name__ == "__main__":
    main(COMPETITION_CODES, SEASONS)
