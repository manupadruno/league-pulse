-- depends: 002.create-teams
-- depends: 003.create-seasons
-- depends: 004.create-matches

CREATE TABLE scorer (
    player_id INT NOT NULL,
    season_id INT NOT NULL,
    team_id INT,
    goals INT,
    assists INT,
    penalties INT,
    PRIMARY KEY (player_id, season_id),
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
    FOREIGN KEY (season_id) REFERENCES season(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES team(id) ON DELETE SET NULL
);