-- depends: 002.create-teams
-- depends: 003.create-seasons

CREATE TABLE match (
    id INT PRIMARY KEY,
    season_id INT NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    utc_date TIMESTAMPTZ,
    last_updated TIMESTAMPTZ,
    status VARCHAR(20) CHECK (status IN ('SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED', 'FINISHED', 'SUSPENDED', 'POSTPONED', 'CANCELLED', 'AWARDED')),
    matchday INT,
    home_score INT,
    away_score INT,
    FOREIGN KEY (season_id) REFERENCES season(id) ON DELETE RESTRICT,
    FOREIGN KEY (home_team_id) REFERENCES team(id) ON DELETE RESTRICT,
    FOREIGN KEY (away_team_id) REFERENCES team(id) ON DELETE RESTRICT 
);