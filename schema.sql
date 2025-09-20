-- SAMUD Database Schema
-- SQLite database for player persistence

-- Players table - stores user accounts and state
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    current_room_id TEXT NOT NULL DEFAULT 'alamo_plaza',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure username is unique (case-insensitive in SQLite by default)
    CONSTRAINT username_unique UNIQUE (username COLLATE NOCASE)
);

-- Index on username for faster login queries
CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);

-- Index on current_room_id for room occupancy queries
CREATE INDEX IF NOT EXISTS idx_players_room ON players(current_room_id);

-- Session tracking table (optional, for future expansion)
-- Tracks active sessions to prevent duplicate logins
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    session_token TEXT UNIQUE,
    ip_address TEXT,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,

    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Index for active session lookups
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(player_id, is_active);

-- Stats table for future expansion (tracking gameplay statistics)
CREATE TABLE IF NOT EXISTS player_stats (
    player_id INTEGER PRIMARY KEY,
    total_playtime INTEGER DEFAULT 0,  -- in seconds
    rooms_visited INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);