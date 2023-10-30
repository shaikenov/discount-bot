CREATE TABLE cart
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id       BIGINT NOT NULL,
    link_id       VARCHAR(100) NOT NULL,
    source        VARCHAR(100) NOT NULL,
    title         VARCHAR(100) NOT NULL,
    price         INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);