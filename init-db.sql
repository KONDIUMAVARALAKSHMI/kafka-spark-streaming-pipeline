-- Create page_view_counts table for tumbling window aggregations
CREATE TABLE IF NOT EXISTS page_view_counts (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    page_url TEXT NOT NULL,
    view_count BIGINT,
    PRIMARY KEY (window_start, window_end, page_url)
);

-- Create active_users table for sliding window aggregations
CREATE TABLE IF NOT EXISTS active_users (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    active_user_count BIGINT,
    PRIMARY KEY (window_start, window_end)
);

-- Create user_sessions table for stateful transformations
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id TEXT PRIMARY KEY,
    session_start_time TIMESTAMP,
    session_end_time TIMESTAMP,
    session_duration_seconds BIGINT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_page_view_counts_window ON page_view_counts(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_active_users_window ON active_users(window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_user_sessions_start_time ON user_sessions(session_start_time);
