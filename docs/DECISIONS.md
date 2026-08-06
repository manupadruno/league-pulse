# Architecture Decision Log

## 2026-08-06 — Empty result set as the "no data" signal, not `currentMatchday`

**Decision**: in `validate_phase`, skip validation for a season when
`get_matchday_clasifications` returns an empty list, rather than trying to
infer "has this season started" from `season.currentMatchday`.

**Why**: discovered that `currentMatchday` is not a reliable signal — the API
can report a matchday greater than 1 for a season that hasn't produced any
finished matches yet. Checking directly whether the system has computed data
to compare against is more accurate, and doubles as a general "no data for
this combination" guard, not just a workaround for one specific case.

---

## 2026-08-06 — Official `/standings` responses are not persisted to the raw layer

**Decision**: `fetch_standings` results are used in-memory for cross-validation
and discarded; unlike `competitions`, `matches` and `scorers`, they are never
written to `data/raw/`.

**Why**: the raw layer exists to serve as the system's reproducible source of
truth — data the pipeline loads and depends on. `/standings` data is never
loaded into any table; it's used once, for a point-in-time comparison against
already-loaded data. Persisting it would add no reproducibility value and
break the pattern's purpose (a raw copy "to load from") without a real use
case behind it.

---

## 2026-07-30 — `RANK()` over `ROW_NUMBER()` for standings position

**Decision**: use `RANK()` when computing `position` in `matchday_clasification`.

**Why**: the system only breaks ties by goal difference — it does not
implement head-to-head results, which the official standings do use. Two
teams tied on points and goal difference are therefore genuinely tied given
the data the system has. `RANK()` reports them as sharing the same position
(with the next rank skipping accordingly), matching that reality. `ROW_NUMBER()`
would assign them distinct, arbitrary positions with no real criterion behind
the ordering — misrepresenting the data as more decisive than it is.

---

## 2026-07-30 — `matchday_clasification` is fully recomputed, not incrementally updated

**Decision**: loading standings for a season means `DELETE FROM
matchday_clasification WHERE season_id = %s` followed by a full `INSERT`
from the CTE-based query, rather than upserting row by row.

**Why**: this table is a derived, fully reproducible snapshot computed from
`match` — it carries no information that isn't already recoverable from the
source tables. Recomputing it wholesale guarantees it can never drift out of
sync with `match` (e.g. after a score correction), at negligible cost given
the data volume involved.

---

## 2026-07-28 — `NULL` in `scorer.assists` / `penalties` is not coerced to `0`

**Decision**: keep `assists` and `penalties` as `Optional[int]` and pass
through `NULL` values from the API as-is, instead of defaulting them to `0`.

**Why**: verified against the official football-data.org documentation, which
states the API uses `null` for values that are not known or not available —
not as an alternate way of encoding zero. Coercing to `0` would assert a fact
("this player has zero penalties") that the source data doesn't actually
state. Same principle already applied to `match.home_score` /
`match.away_score` for unplayed fixtures.

---

## 2026-07-28 — All-or-nothing atomicity for `team`, row-by-row for `season`

**Decision**: `load_teams` executes all inserts for a competition-year inside
a single transaction (one `commit()` at the end); `load_seasons` commits each
`season` independently.

**Why**: a partial set of teams for a league is actively harmful — it would
silently corrupt every match and standings computation that depends on it, so
`team` inserts must succeed completely or not at all. A single season failing
to load, by contrast, doesn't invalidate the others; isolating each one lets
the pipeline keep the seasons that did succeed. The atomicity boundary is
chosen per entity based on the real cost of a partial write, not applied
uniformly.

---

## 2026-07-28 — `ON CONFLICT DO UPDATE` (upsert) instead of plain `INSERT`

**Decision**: every `load_*` function uses `INSERT ... ON CONFLICT (...) DO
UPDATE SET ...` rather than a bare `INSERT`.

**Why**: the same team or player can legitimately appear across multiple
competition-year combinations (e.g. a team playing in both a domestic league
and a cup). Without upsert semantics, reprocessing would fail on duplicate
primary keys. Upserting also makes the pipeline safely re-runnable — loading
the same data twice updates rather than errors.

---

## 2026-07-28 — Single reused connection, commit managed per function

**Decision**: one `psycopg` connection is opened once in `main()` and passed
as a parameter to every `load_*` / `get_*` function; each function manages
its own `commit()` rather than relying on `with connection as conn:` (which
would close the connection after first use).

**Why**: opening a new connection per operation would be needlessly expensive
and would work against reusing the connection across the whole pipeline run.
Committing at the function level (instead of one global commit) keeps each
unit of work — one team, one match batch, one standings recomputation — as
its own atomic operation, consistent with the per-entity atomicity decisions
above.

---

## 2026-07-22 — Deliberate exclusion of low-value fields

**Decision**: fields such as competition `area`/country, season `stages`,
and player `position` / `shirtNumber` / `nationality` / `lastUpdated` are
present in the raw API responses but intentionally excluded from the
Pydantic models and the database schema.

**Why**: none has an identified use within the project's current scope
(league standings by matchday). Extracting them isn't technically harder than
the fields that were kept (e.g. `crest`, kept specifically for a plausible
future dashboard) — the difference is that no concrete use case justifies
carrying them. Since the raw layer keeps the full original response, none of
this data is actually lost; it can be added later without re-extracting
anything.

---

## 2026-07-22 — No bridge table between `team` and `competition`

**Decision**: there is no `team_competition` join table, even though the
conceptual relationship is many-to-many.

**Why**: the relationship is fully derivable — a team's participation in a
competition-season is already implied by the matches it plays in, which
reference both `team` and `season` (which in turn references `competition`).
Materializing it separately would duplicate state that can always be
recovered with a `JOIN`, and — worse — the derived table itself can't be
populated reliably before matches exist, meaning by the time it _could_ be
correct, it's no longer needed.

---

## 2026-07-22 — Composite primary key on `scorer`

**Decision**: `scorer`'s primary key is `(player_id, season_id)`, not a
synthetic `SERIAL id`.

**Why**: the API's scorers endpoint doesn't provide any identifier for a
"player-in-a-season" record — confirmed by inspecting the real response.
`(player_id, season_id)` is the natural, already-unique identity of the row;
inventing a surrogate `id` would add nothing and would require synthesizing a
value the source data doesn't provide.

---

## 2026-07-22 — Per-relationship `ON DELETE` policy, not a single default

**Decision**: `ON DELETE` is chosen per foreign key based on the real
consequence of that specific deletion, not applied uniformly:

- `RESTRICT` — `match.season_id`, `match.home_team_id` / `away_team_id`
  (deleting a team or season should never silently discard match history).
- `SET NULL` — `season.winner_id` (losing the "who won" reference is
  acceptable; the season itself still matters).
- `CASCADE` — `scorer.player_id`, `scorer.season_id` (a scorer row with no
  player or season behind it is meaningless on its own).

**Why**: applying one blanket policy (e.g. always `RESTRICT`) would either
block legitimate cleanup or, if always `CASCADE`, risk deleting valuable
history by accident. Reasoning about each relationship's actual business
meaning gives a schema that protects what matters and doesn't block what
doesn't.

---

## 2026-07-22 — Migrations already applied are treated as immutable

**Decision**: once a Yoyo migration has been applied, its `.sql` file is never
edited in place. Fixing a mistake means either rolling back, editing, and
reapplying, or writing a brand-new migration.

**Why**: learned the hard way — Yoyo stores a hash of each migration's content
at apply time; editing an already-applied file after the fact makes the hash
mismatch, and Yoyo stops recognizing it as applied even though the schema
change is still live in Postgres. This desyncs Yoyo's tracking from the real
database state and can produce confusing dependency errors. Treating applied
migrations as append-only, like committed git history, avoids the problem
entirely.

---

## 2026-07-22 — Yoyo for migrations, not raw SQL scripts or an ORM's migration tool

**Decision**: use `yoyo-migrations` to manage schema changes as versioned,
dependency-ordered SQL files with a tracking table, instead of hand-run `.sql`
scripts or an ORM-coupled tool like Alembic.

**Why**: hand-run scripts require manually remembering what's been applied
and in what order — exactly the kind of state-tracking problem a dedicated
tool solves for free. Alembic would have coupled schema management to
SQLAlchemy, which was already ruled out in favor of raw SQL (see below).
Yoyo manages the same apply/rollback/dependency bookkeeping while leaving the
actual SQL fully hand-written.

---

## 2026-07-21 — PostgreSQL via Docker Compose

**Decision**: run PostgreSQL as a Docker Compose service (`postgres:16`)
instead of installing it directly on the host system, with the port mapped to
`${POSTGRES_PORT}` (not the standard 5432) and a named volume for
persistence.

**Why**:

- **Version reproducibility**: anyone cloning the repo (including myself a
  year from now, or an interviewer) gets the exact same Postgres version via
  `docker compose up`, regardless of what's installed on their system.
- **Clean resets**: schema changes and failed experiments during development
  mean recreating the database often. `docker compose down -v` wipes it
  cleanly without touching anything else on the system — far more delicate to
  do with a native install.
- **One-command evaluation**: the whole stack comes up with a single command,
  so anyone reviewing the project doesn't need to install Postgres locally.
- **Production parity**: on AWS this will talk to a containerized or managed
  Postgres, not a manually installed one — developing against a container
  already narrows that gap.

**Non-standard port**: avoids clashing with any Postgres instance that might
already exist (or later get installed) directly on the host.

**Version 16 over 18**: no feature in Postgres 18 is needed for this project,
and 16 has more mileage with the wider ecosystem (drivers, tooling,
community troubleshooting) — less friction while learning Docker and
Postgres at the same time. Also confirmed the two versions differ in their
default data directory path, which would have silently broken the volume
mount if mixed up.

---

## 2026-07-21 — `psycopg` (raw SQL) instead of SQLAlchemy

**Decision**: use `psycopg` with hand-written SQL for the load layer, instead
of an ORM like SQLAlchemy.

**Why**: this roadmap's stated goal from the start is to get genuinely fluent
in SQL — joins, CTEs, window functions, execution plans, optimization. An ORM
abstracts away exactly what I want to practice. I'd already used SQLAlchemy
at work without getting much value from its abstractions; for a learning
project, writing and understanding real SQL in every insert and query
outweighs the productivity an ORM would add.

---

## 2026-07-14 — Raw layer filenames: timestamp before domain

**Decision**: `data/raw/{entity}/{timestamp}_{identifier}.json`, not
`{identifier}_{timestamp}.json`.

**Why**: what matters in the raw layer is extraction lineage — when each file
was pulled, for auditing and debugging the pipeline itself. In the
silver/gold layers, the relevant grouping shifts to domain (competition,
season), which is how that data actually gets queried for analysis.

---

## 2026-07-13 — `uv` for environment and package management

**Decision**: use `uv` instead of `pip + venv`.

**Why**: deterministic lockfile, faster, an increasingly common standard in
2026 — and a new tool worth learning.

---

## 2026-07-13 — `requests` as the HTTP client library

**Decision**: use `requests` instead of `httpx`.

**Why**: the project doesn't need asynchronous calls, so the simpler library
was preferred (YAGNI — no benefit today from `httpx`'s main differentiator).

---

## 2026-07-13 — Module responsibility separation (extract / raw / main)

**Decision**: split the pipeline into single-responsibility modules with no
direct dependencies between them: `extract.py` only knows how to talk to the
API (build the request, authenticate, return JSON); `raw.py` only knows how
to persist an already-obtained dictionary to disk; neither imports or calls
the other. `main.py` is the only module that knows about both and orchestrates
the full flow (calls `extract`, passes the result to `raw`).

Within `extract.py`, `response.raise_for_status()` is used instead of
manually checking `response.status_code` — it raises a specific, recognizable
exception (`requests.exceptions.HTTPError`) on API errors, instead of a
generic condition that would need to be duplicated in every function.

**Why**: each module changes for different reasons and at different rates. If
the data source changes tomorrow (a different football API), the change
should stay contained in `extract.py` without touching how data is stored. If
where the raw layer lives changes tomorrow (local disk to S3, say), the
change should stay contained in `raw.py` without touching how data is
extracted.

Having `save_raw` receive an already-obtained dictionary as a parameter
(instead of calling `fetch_*` internally) is what makes this real: it allows
testing persistence with a hand-written sample dictionary, without depending
on a real HTTP call every time, and lets `save_raw` be reused with data that
might come from any other source in the future.

---

## 2026-07-13 — Raw layer design

**Decision**: the raw layer stores a faithful, untransformed copy of whatever
the API returns, following these rules:

- The **full** response is stored, including metadata like `resultSet`
  (match count, played, dates) — not just the `matches` array that looks like
  "the important part" today.
- Stored as **JSON files on disk**, not in a PostgreSQL table.
- **Nothing is filtered** at this layer (e.g. by `status = FINISHED`) —
  filtering is `transform.py`'s responsibility.
- `season` is a **required** parameter in `fetch_matches`, with no default
  falling back to the API's "current season".
- Filename pattern: `data/raw/{entity}/{timestamp}_{identifier}.json`, with
  the **timestamp first**.
- The timestamp is generated in **UTC** (`datetime.now(timezone.utc)`), not
  local time.
- `data/` is excluded from git.

**Why**: all of these decisions serve the same underlying idea — the raw
layer is the pipeline's reproducible source of truth, and its value depends
on being an exact, complete copy of what existed at a given moment, with no
business opinions baked in yet.

- Storing the full response avoids having to re-request data from the API
  (10 req/min rate limit) if something that looks dispensable today (like
  `resultSet`) turns out to be useful later — e.g. to validate no match is
  missing.
- JSON tolerates API shape changes (schema-on-read): if a field appears or
  disappears tomorrow, the file simply reflects it. A fixed-schema Postgres
  table (schema-on-write) would fail the insert or silently drop the new
  field, losing information without warning.
- Not filtering by `status` at extraction time keeps the raw layer neutral:
  deciding which matches are "useful" is a business decision that belongs in
  the transform layer, not extraction.
- Requiring `season` explicitly prevents the same code, run at different
  times, from returning different data without the caller having asked for
  that — necessary to reproduce a specific season's history.
- Timestamp-first filenames match how this layer is actually queried: in raw,
  what matters is **when** each piece of data was extracted (for auditing and
  debugging the pipeline itself), while later layers (silver/gold) are
  queried by domain (competition, season) for analysis.
- UTC avoids timezone drift if the pipeline moves from running locally
  (Madrid time, with seasonal DST shifts) to running on a cloud server
  (typically UTC by default).
- `data/` stays out of git for three reasons: data protection, repository
  size/cost, and because git isn't designed to version constantly changing
  data (every commit would duplicate the full history).
