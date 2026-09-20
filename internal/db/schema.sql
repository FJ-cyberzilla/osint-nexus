-- PostgreSQL DDL for Behavioral Profiling System

CREATE TABLE IF NOT EXISTS profiles (
    profile_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES profiles(profile_id),
    device_type VARCHAR(50) NOT NULL,
    ip_subnet_hash VARCHAR(64) NOT NULL,
    tls_fingerprint_hash VARCHAR(64) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds FLOAT,
    INDEX idx_sessions_profile_id (profile_id),
    INDEX idx_sessions_start_time (start_time)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    INDEX idx_telemetry_events_session_id (session_id),
    INDEX idx_telemetry_events_created_at (created_at)
);
