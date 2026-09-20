package db

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// ProfilingRepository handles database operations for target profiles and sessions.
type ProfilingRepository struct {
	pool *pgxpool.Pool
}

// NewProfilingRepository initializes a new ProfilingRepository.
func NewProfilingRepository(pool *pgxpool.Pool) *ProfilingRepository {
	return &ProfilingRepository{
		pool: pool,
	}
}

// Profile represents a target profile.
type Profile struct {
	ProfileID      uuid.UUID
	CreatedAt      string
	ConfidenceScore float64
	Metadata       []byte // JSONB
}

// CreateProfile inserts a new profile into the database.
func (r *ProfilingRepository) CreateProfile(ctx context.Context, profileID uuid.UUID, confidence float64, metadata []byte) error {
	query := `INSERT INTO profiles (profile_id, confidence_score, metadata) VALUES ($1, $2, $3)`
	_, err := r.pool.Exec(ctx, query, profileID, confidence, metadata)
	if err != nil {
		return fmt.Errorf("db: create profile: %w", err)
	}
	return nil
}

// GetProfile retrieves a profile by ID.
func (r *ProfilingRepository) GetProfile(ctx context.Context, profileID uuid.UUID) (*Profile, error) {
	query := `SELECT profile_id, created_at, confidence_score, metadata FROM profiles WHERE profile_id = $1`
	row := r.pool.QueryRow(ctx, query, profileID)

	var p Profile
	err := row.Scan(&p.ProfileID, &p.CreatedAt, &p.ConfidenceScore, &p.Metadata)
	if err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("db: get profile: %w", err)
	}
	return &p, nil
}

// Session represents a connection session.
type Session struct {
	SessionID         uuid.UUID
	ProfileID         uuid.UUID
	DeviceType        string
	IPSubnetHash      string
	TLSFingerprintHash string
	StartTime         string
}

// AddSession inserts a new session into the database.
func (r *ProfilingRepository) AddSession(ctx context.Context, s *Session) error {
	query := `INSERT INTO sessions (session_id, profile_id, device_type, ip_subnet_hash, tls_fingerprint_hash, start_time) 
	          VALUES ($1, $2, $3, $4, $5, $6)`
	_, err := r.pool.Exec(ctx, query, s.SessionID, s.ProfileID, s.DeviceType, s.IPSubnetHash, s.TLSFingerprintHash, s.StartTime)
	if err != nil {
		return fmt.Errorf("db: add session: %w", err)
	}
	return nil
}
