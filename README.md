# league-pulse

End-to-end batch data pipeline that extracts football match data, computes league
standings from scratch using SQL window functions, and cross-validates the result
against the official standings API.

Built as a portfolio project to demonstrate production-grade data engineering
practices — not just moving data from A to B, but designing, validating, and
reasoning about a system end to end.

## Highlights

- **Full pipeline**: extract → raw storage → transform → load → derived computation → validation
- **Standings computed from raw match data**, not fetched — using CTEs and window
  functions (`SUM() OVER`, `RANK()`) to build cumulative points, goal difference and
  position, matchday by matchday
- **Cross-validated against the official API**: 0 discrepancies across two full
  Premier League seasons (2023/24, 2024/25)
- **Type-safe throughout**: every entity is a validated Pydantic model, from raw JSON
  to database row
- **Idempotent by design**: upserts (`ON CONFLICT`), isolated failure handling per
  unit of work — one bad record never takes down the rest
- **Dockerized PostgreSQL** with versioned, reviewable SQL migrations (Yoyo)

## Architecture

```
football-data.org API
        │
        ▼
   extract  ──► raw JSON on disk (schema-on-read, immutable, replayable)
        │
        ▼
   transform ──► typed Pydantic models (Competition, Team, Season, Match, Player, Scorer)
        │
        ▼
     load    ──► PostgreSQL (upsert, FK-consistent load order)
        │
        ▼
  clasificacion_jornada ──► computed via SQL window functions from `match`
        │
        ▼
   validate  ──► compared against official /standings endpoint
```

## Data model

| Table                    | Purpose                                                          |
| ------------------------ | ---------------------------------------------------------------- |
| `competition`            | League metadata                                                  |
| `team`                   | Teams (deduplicated across matches)                              |
| `season`                 | One row per competition-year, own lifecycle                      |
| `match`                  | Match facts: two FKs to `team` (home/away), no bridge table      |
| `player`, `scorer`       | Top scorers per season (N:1 player → scorer)                     |
| `matchday_clasification` | Derived standings snapshot, one row per (season, team, matchday) |

Full schema, FK constraints and `ON DELETE` policies live in `migrations/`.

## Tech stack

Python · PostgreSQL · Docker Compose · Yoyo (migrations) · Pydantic · psycopg3 · uv · requests

## Key engineering decisions

- Raw layer stored as JSON, not SQL — schema-on-read tolerates upstream API changes
  without breaking the pipeline
- `RANK()` over `ROW_NUMBER()` for standings position — the system doesn't implement
  head-to-head tiebreakers, so tied teams are reported as tied rather than given an
  arbitrary order
- No bridge table for `team` ↔ `competition` — the relationship is fully derivable
  from `match`, avoiding redundant state
- Each pipeline phase (extract / transform / load / validate) is independently
  runnable and independently fails without cascading

Full rationale for every decision in [`DECISIONS.md`](./docs/DECISIONS.md).

## Known limitations

- Free-tier API access: limited competitions, 3-year match history, 10 calls/minute
- Standings position may legitimately differ from the official table when teams are
  tied on points and goal difference (head-to-head not implemented — see above)

## Getting started

```bash
git clone <repo-url>
cd league-pulse
uv sync
cp .env.example .env        # fill in your football-data.org token and Postgres creds
docker compose up -d
uv run yoyo apply
uv run src/league_pulse/main.py
```

## Status

- [x] Extraction, raw storage, transformation (all entities)
- [x] PostgreSQL schema with versioned migrations
- [x] Load pipeline with upsert + isolated error handling
- [x] Standings computation (window functions)
- [x] Cross-validation against official API
- [ ] Airflow orchestration
- [ ] Containerized application (currently only Postgres runs in Docker)
- [ ] AWS deployment
