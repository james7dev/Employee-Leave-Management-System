CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('employee','manager','hr','admin')),
    department  TEXT    NOT NULL,
    manager_id  INTEGER REFERENCES users(id),
    is_active   INTEGER NOT NULL DEFAULT 1,
    date_joined TEXT    DEFAULT (date('now')),
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leave_types (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT    UNIQUE NOT NULL,
    annual_quota            INTEGER NOT NULL,
    requires_hr             INTEGER NOT NULL DEFAULT 0,
    requires_document       INTEGER NOT NULL DEFAULT 0,
    max_consecutive_days    INTEGER,
    notice_period_days      INTEGER NOT NULL DEFAULT 0,
    carry_forward_allowed   INTEGER NOT NULL DEFAULT 0
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
    reason          TEXT,
    status          TEXT    NOT NULL DEFAULT 'Pending Manager',
    manager_id      INTEGER REFERENCES users(id),
    hr_id           INTEGER REFERENCES users(id),
    submitted_at    TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leave_approvals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    leave_request_id    INTEGER NOT NULL REFERENCES leave_requests(id),
    approver_id         INTEGER NOT NULL REFERENCES users(id),
    role                TEXT    NOT NULL,
    action              TEXT    NOT NULL,
    comment             TEXT,
    timestamp           TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leave_documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    leave_request_id    INTEGER NOT NULL REFERENCES leave_requests(id),
    file_path           TEXT    NOT NULL,
    uploaded_at         TEXT    DEFAULT (datetime('now'))
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

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id),
    action      TEXT    NOT NULL,
    target_id   INTEGER,
    timestamp   TEXT    DEFAULT (datetime('now'))
);
