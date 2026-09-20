package db

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

// PostgresEngine implements the database engine using PostgreSQL (pgxpool).
type PostgresEngine struct {
	pool *pgxpool.Pool
}

// NewPostgresEngine initializes a new PostgreSQL engine with pgxpool.
func NewPostgresEngine(ctx context.Context, connString string) (*PostgresEngine, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, fmt.Errorf("db: create pgxpool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("db: ping postgres: %w", err)
	}

	return &PostgresEngine{
		pool: pool,
	}, nil
}

// Pool returns the underlying pgxpool instance.
func (e *PostgresEngine) Pool() *pgxpool.Pool {
	return e.pool
}

// Close closes the database pool.
func (e *PostgresEngine) Close() {
	e.pool.Close()
}
