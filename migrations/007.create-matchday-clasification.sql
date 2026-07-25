-- depends: 002.create-teams
-- depends: 003.create-seasons

CREATE TABLE matchday_clasification (
    season_id INT NOT NULL,
    team_id INT NOT NULL,
    matchday INT NOT NULL,
    points INT NOT NULL,
    wins INT NOT NULL,
    draws INT NOT NULL,
    losses INT NOT NULL,
    goals_for INT NOT NULL,
    goals_against INT NOT NULL,
    goal_difference INT GENERATED ALWAYS AS (goals_for - goals_against) STORED,
    position INT,
    PRIMARY KEY (season_id, team_id, matchday),
    FOREIGN KEY (season_id) REFERENCES season(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES team(id) ON DELETE CASCADE
);