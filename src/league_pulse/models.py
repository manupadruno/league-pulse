from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    scheduled = "SCHEDULED"
    timed = "TIMED"
    in_play = "IN_PLAY"
    paused = "PAUSED"
    finished = "FINISHED"
    suspended = "SUSPENDED"
    postponed = "POSTPONED"
    cancelled = "CANCELLED"
    awarded = "AWARDED"


class Stage(str, Enum):
    final = "FINAL"
    third_place = "THIRD_PLACE"
    semi_finals = "SEMI_FINALS"
    quarter_finals = "QUARTER_FINALS"
    last_16 = "LAST_16"
    last_32 = "LAST_32"
    last_64 = "LAST_64"
    round_4 = "ROUND_4"
    round_3 = "ROUND_3"
    round_2 = "ROUND_2"
    round_1 = "ROUND_1"
    group_stage = "GROUP_STAGE"
    preliminary_round = "PRELIMINARY_ROUND"
    qualification = "QUALIFICATION"
    qualification_round_1 = "QUALIFICATION_ROUND_1"
    qualification_round_2 = "QUALIFICATION_ROUND_2"
    qualification_round_3 = "QUALIFICATION_ROUND_3"
    playoff_round_1 = "PLAYOFF_ROUND_1"
    playoff_round_2 = "PLAYOFF_ROUND_2"
    playoffs = "PLAYOFFS"
    regular_season = "REGULAR_SEASON"
    clausura = "CLAUSURA"
    apertura = "APERTURA"
    championship_round = "CHAMPIONSHIP_ROUND"
    relegation_round = "RELEGATION_ROUND"


class Team(BaseModel):
    id: int
    name: str
    shortName: str
    tla: str
    crest: str


class Match(BaseModel):
    id: int
    competitionId: int
    utcDate: datetime
    status: MatchStatus
    matchday: int | None
    stage: Stage
    group: str | None
    lastUpdated: datetime
    homeTeamId: int
    awayTeamId: int
    homeScore: int | None
    awayScore: int | None
