CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('employee','manager','hr')),
    department  TEXT    NOT NULL,
    manager_id  INTEGER REFERENCES users(id),
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leave_types (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    UNIQUE NOT NULL,
    max_days_per_year   INTEGER NOT NULL,
    requires_approval   INTEGER NOT NULL DEFAULT 1,
    requires_docs       INTEGER NOT NULL DEFAULT 0,
    is_paid             INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS leave_balances (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    leave_type_id   INTEGER NOT NULL REFERENCES leave_types(id),
    year            INTEGER NOT NULL,
    total_days      REAL    NOT NULL,
    used_days       REAL    NOT NULL DEFAULT 0,
    UNIQUE(user_id, leave_type_id, year)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     INTEGER NOT NULL REFERENCES users(id),
    leave_type_id   INTEGER NOT NULL REFERENCES leave_types(id),
    start_date      TEXT    NOT NULL,
    end_date        TEXT    NOT NULL,
    working_days    REAL    NOT NULL,
    is_half_day     INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'Pending'
                    CHECK(status IN ('Pending','Approved','Rejected','Cancelled')),
    reason          TEXT,
    manager_note    TEXT,
    submitted_at    TEXT    DEFAULT (datetime('now')),
    actioned_at     TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    message     TEXT    NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS public_holidays (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT UNIQUE NOT NULL,
    name    TEXT NOT NULL
);
