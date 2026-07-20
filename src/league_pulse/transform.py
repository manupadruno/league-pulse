from models import Match, MatchStatus
from raw import load_raw


def parse_match(raw_match: dict) -> Match:
    return Match(
        id=raw_match["id"],
        competitionId=raw_match["competition"]["id"],
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
