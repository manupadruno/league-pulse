from models import Standing, MatchdayClasification
from dataclasses import dataclass


@dataclass
class Discrepancy:
    team_id: int
    field: str
    expected: int | None  # the official value (standing)
    actual: int | None   # our value (matchday_clasification)


standing_fields = ["won", "draw",
                   "lost", "points", "goalsFor", "goalsAgainst"]
standing_vs_matchday = {
    "won": "wins",
    "draw": "draws",
    "lost": "losses",
    "points": "points",
    "goalsFor": "goalsFor",
    "goalsAgainst": "goalsAgainst"
}


def validate_table(standings: list[Standing], matchday_clasifications: list[MatchdayClasification]) -> list[Discrepancy]:
    discrepancies = []
    for standing in standings:
        team_id = standing.teamId
        matchday_clasification = next(
            (mc for mc in matchday_clasifications if mc.teamId == team_id), None)

        if matchday_clasification is None:
            discrepancies.append(Discrepancy(
                team_id=team_id,
                field="existence",
                expected=None,
                actual=None
            ))
            continue

        # compares each basic field (won, draw, lost, points, goalsFor, goalsAgainst)
        # for each field that does not equals, adds a Discrepancy to the list
        for field in standing_fields:
            standing_value = getattr(standing, field)
            matchday_clasification_value = getattr(
                matchday_clasification, standing_vs_matchday[field])
            if standing_value != matchday_clasification_value:
                discrepancies.append(Discrepancy(
                    team_id=team_id,
                    field=field,
                    expected=standing_value,
                    actual=matchday_clasification_value
                ))

        # position may be different as we do not take into account direct confrontations between teams tied on points
        if standing.position != matchday_clasification.position:
            discrepancies.append(Discrepancy(
                team_id=team_id,
                field="position",
                expected=standing.position,
                actual=matchday_clasification.position
            ))

    return discrepancies


def report_discrepancies(discrepancies: list[Discrepancy]) -> None:
    for discrepancy in discrepancies:
        if discrepancy.field == "existence":
            print(
                f"ERROR: team {discrepancy.team_id} exists in official standings "
                f"but is missing from matchday_clasification")
        elif discrepancy.field == "position":
            print(
                f"WARNING: team {discrepancy.team_id} position differs "
                f"(official: {discrepancy.expected}, calculated: {discrepancy.actual}) "
                f"- likely due to head-to-head tiebreaker not implemented")
        else:
            print(
                f"ERROR: team {discrepancy.team_id} field '{discrepancy.field}' mismatch "
                f"(official: {discrepancy.expected}, calculated: {discrepancy.actual})")
