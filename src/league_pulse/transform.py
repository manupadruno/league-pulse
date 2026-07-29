from models import Match, MatchStatus, Player, Scorer, Team, Competition, Season
from raw import load_raw
from datetime import datetime


def parse_match(raw_match: dict) -> Match:
    return Match(
        id=raw_match["id"],
        seasonId=raw_match["season"]["id"],
        utcDate=raw_match["utcDate"],
        status=raw_match["status"],
        matchday=raw_match["matchday"],
        stage=raw_match["stage"],
        group=raw_match["group"],
        lastUpdated=raw_match["lastUpdated"],
        homeTeamId=raw_match["homeTeam"]["id"],
        awayTeamId=raw_match["awayTeam"]["id"],
        homeScore=raw_match.get("score", {}).get("fullTime", {}).get("home"),
        awayScore=raw_match.get("score", {}).get("fullTime", {}).get("away")
    )


def parse_matches(raw_matches: list[dict]) -> list[Match]:
    raw_matches_filtered = [
        match for match in raw_matches if match["status"] == MatchStatus.finished]
    return [parse_match(match) for match in raw_matches_filtered]


def load_and_parse_matches(competition_code: str, season: int) -> list[Match]:
    identifier_prefix = f"{competition_code}_{season}"
    raw_dict = load_raw("matches", identifier_prefix)
    matches = raw_dict["matches"]
    return parse_matches(matches)


def parse_team(raw_team: dict) -> Team:
    return Team(
        id=raw_team["id"],
        name=raw_team["name"],
        shortName=raw_team["shortName"],
        tla=raw_team["tla"],
        crest=raw_team["crest"]
    )


def parse_teams(raw_teams: list[dict]) -> list[Team]:
    return [parse_team(team) for team in raw_teams]


def load_and_parse_teams(competition_code: str, season: int) -> list[Team]:
    identifier_prefix = f"{competition_code}_{season}"
    raw_dict = load_raw("matches", identifier_prefix)
    matches = raw_dict["matches"]
    teams = {}
    for match in matches:
        home_team = match["homeTeam"]
        away_team = match["awayTeam"]
        teams[home_team["id"]] = home_team
        teams[away_team["id"]] = away_team
    return parse_teams(list(teams.values()))


def parse_competition(raw_competition: dict) -> Competition:
    return Competition(
        id=raw_competition["id"],
        name=raw_competition["name"],
        type=raw_competition["type"],
        code=raw_competition["code"],
        emblem=raw_competition["emblem"],
    )


def load_and_parse_competition(competition_code: str) -> Competition:
    identifier_prefix = f"{competition_code}"
    competition_dict = load_raw("competitions", identifier_prefix)
    return parse_competition(competition_dict)


def parse_season(raw_season: dict, competition_id: int) -> Season:
    winner = raw_season.get(
        "winner")
    return Season(
        id=raw_season["id"],
        competitionId=competition_id,
        startDate=raw_season["startDate"],
        endDate=raw_season["endDate"],
        currentMatchday=raw_season["currentMatchday"],
        winnerId=None if winner is None else winner.get("id"),
    )


def parse_seasons(raw_seasons: list[dict], years: list[int], competition_id: int) -> list[Season]:
    raw_seasons_filtered = [
        season for season in raw_seasons if datetime.strptime(season["startDate"], "%Y-%m-%d").year in years]
    return [parse_season(season, competition_id) for season in raw_seasons_filtered]


def load_and_parse_seasons(competition_code: str, years: list[int]) -> list[Season]:
    raw_dict = load_raw("competitions", competition_code)
    competition_id = raw_dict["id"]
    raw_seasons = raw_dict["seasons"]
    return parse_seasons(raw_seasons, years, competition_id)


def parse_player(raw_player: dict) -> Player:
    return Player(
        id=raw_player["id"],
        name=raw_player["name"],
        firstName=raw_player["firstName"],
        lastName=raw_player["lastName"],
        dateOfBirth=raw_player["dateOfBirth"]
    )


def parse_players(raw_players: list[dict]) -> list[Player]:
    return [parse_player(player) for player in raw_players]


def load_and_parse_players(competition_code: str, year: int) -> list[Player]:
    identifier_prefix = f"{competition_code}_{year}"
    raw_dict = load_raw("scorers", identifier_prefix)
    scorers = raw_dict["scorers"]
    players = [scorer["player"] for scorer in scorers]
    return parse_players(players)


def parse_scorer(raw_scorer: dict, season_id: int) -> Scorer:
    return Scorer(
        playerId=raw_scorer["player"]["id"],
        seasonId=season_id,
        teamId=raw_scorer["team"]["id"],
        goals=raw_scorer["goals"],
        assists=raw_scorer["assists"],
        penalties=raw_scorer["penalties"]
    )


def parse_scorers(raw_scorers: list[dict], season_id: int) -> list[Scorer]:
    return [parse_scorer(scorer, season_id) for scorer in raw_scorers]


def load_and_parse_scorers(competition_code: str, year: int) -> list[Scorer]:
    identifier_prefix = f"{competition_code}_{year}"
    raw_dict = load_raw("scorers", identifier_prefix)
    season_id = raw_dict["season"]["id"]
    scorers = raw_dict["scorers"]
    return parse_scorers(scorers, season_id)
