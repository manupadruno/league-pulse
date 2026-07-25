-- depends: 001.create-competitions
-- depends: 002.create-teams

CREATE TABLE season (
    id INT PRIMARY KEY,
    competition_id INT NOT NULL,
    start_date DATE,
    end_date DATE,
    current_matchday INT,
    winner_id INT,
    FOREIGN KEY (competition_id) REFERENCES competition(id) ON DELETE RESTRICT,
    FOREIGN KEY (winner_id) REFERENCES team(id) ON DELETE SET NULL
);