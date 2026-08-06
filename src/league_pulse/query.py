import psycopg
from models import MatchdayClasification, Season


def get_matchday_clasifications(connection: psycopg.Connection, season_id: int, matchday: int) -> list[MatchdayClasification]:
    matchday_clasifications: list[MatchdayClasification] = []
    with connection.cursor() as cur:
        cur.execute(
            """SELECT * from matchday_clasification where
                season_id = %s and matchday = %s""",
            (season_id, matchday)
        )
        rows = cur.fetchall()
        for row in rows:
            matchday_clasifications.append(
                MatchdayClasification(
                    seasonId=season_id,
                    teamId=row["team_id"],
                    matchday=row["matchday"],
                    points=row["points"],
                    wins=row["wins"],
                    draws=row["draws"],
                    losses=row["losses"],
                    goalsFor=row["goals_for"],
                    goalsAgainst=row["goals_against"],
                    goalDifference=row["goal_difference"],
                    position=row["position"],
                )
            )
    return matchday_clasifications


def get_seasons(connection: psycopg.Connection, competition_code: str) -> list[Season]:
    seasons: list[Season] = []
    with connection.cursor() as cur:
        cur.execute(
            """SELECT
            s.id, s.competition_id, s.start_date, s.end_date, s.current_matchday, s.winner_id
            from season s
            INNER JOIN competition c on s.competition_id = c.id
            where c.code = %s""",
            (competition_code,)
        )
        rows = cur.fetchall()
        for row in rows:
            seasons.append(
                Season(
                    id=row["id"],
                    competitionId=row["competition_id"],
                    startDate=row["start_date"],
                    endDate=row["end_date"],
                    currentMatchday=row["current_matchday"],
                    winnerId=row["winner_id"],
                )
            )
    return seasons
