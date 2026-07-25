CREATE TABLE competition (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(100),
    code VARCHAR(3) UNIQUE,
    emblem VARCHAR(2083)
);