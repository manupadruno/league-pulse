import psycopg
from config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
from models import Competition, Match, Player, Scorer, Season, Team


def get_connection():
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB
    )


def load_competition(connection: psycopg.Connection, competition: Competition) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """INSERT INTO competition (id, name, type, code, emblem)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET
               name = EXCLUDED.name,
               type = EXCLUDED.type,
               code = EXCLUDED.code,
               emblem = EXCLUDED.emblem""",
            (competition.id, competition.name, competition.type,
             competition.code, competition.emblem)
        )
    connection.commit()


def load_season(connection: psycopg.Connection, season: Season) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """INSERT INTO season (id, competition_id, start_date, end_date, current_matchday, winner_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                competition_id = EXCLUDED.competition_id,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                current_matchday = EXCLUDED.current_matchday,
                winner_id = EXCLUDED.winner_id""",
            (season.id, season.competitionId, season.startDate,
             season.endDate, season.currentMatchday, season.winnerId)
        )
    connection.commit()


def load_seasons(connection: psycopg.Connection, seasons: list[Season]) -> None:
    for season in seasons:
        load_season(connection, season)


def load_teams(connection: psycopg.Connection, teams: list[Team]) -> None:
    with connection.cursor() as cur:
        for team in teams:
            cur.execute(
                """INSERT INTO team (id, name, short_name, tla, crest)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    short_name = EXCLUDED.short_name,
                    tla = EXCLUDED.tla,
                    crest = EXCLUDED.crest""",
                (team.id, team.name, team.shortName,
                 team.tla, team.crest)
            )
    connection.commit()


def load_matches(connection: psycopg.Connection, matches: list[Match]) -> None:
    with connection.cursor() as cur:
        for match in matches:
            cur.execute(
                """INSERT INTO match (id, season_id, home_team_id, away_team_id, utc_date, last_updated, status, matchday, home_score, away_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    season_id = EXCLUDED.season_id,
                    home_team_id = EXCLUDED.home_team_id,
                    away_team_id = EXCLUDED.away_team_id,
                    utc_date = EXCLUDED.utc_date,
                    last_updated = EXCLUDED.last_updated,
                    status = EXCLUDED.status,
                    matchday = EXCLUDED.matchday,
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score
                    """,
                (match.id, match.seasonId, match.homeTeamId,
                 match.awayTeamId, match.utcDate, match.lastUpdated,
                 match.status, match.matchday, match.homeScore,
                 match.awayScore)
            )
    connection.commit()


def load_players(connection: psycopg.Connection, players: list[Player]) -> None:
    with connection.cursor() as cur:
        for player in players:
            cur.execute(
                """INSERT INTO player (id, name, first_name, last_name, date_of_birth)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    date_of_birth = EXCLUDED.date_of_birth""",
                (player.id, player.name, player.firstName,
                 player.lastName, player.dateOfBirth)
            )
    connection.commit()


def load_scorers(connection: psycopg.Connection, scorers: list[Scorer]) -> None:
    with connection.cursor() as cur:
        for scorer in scorers:
            cur.execute(
                """INSERT INTO scorer (player_id, season_id, team_id, goals, assists, penalties)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_id, season_id) DO UPDATE SET
                    team_id = EXCLUDED.team_id,
                    goals = EXCLUDED.goals,
                    assists = EXCLUDED.assists,
                    penalties = EXCLUDED.penalties""",
                (scorer.playerId, scorer.seasonId, scorer.teamId,
                 scorer.goals, scorer.assists, scorer.penalties)
            )
    connection.commit()
