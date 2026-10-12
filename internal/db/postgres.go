package db

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rotisserie/eris"
)

// PostgresEngine implements the database engine using PostgreSQL (pgxpool).
type PostgresEngine struct {
	pool *pgxpool.Pool
}

// NewPostgresEngine initializes a new PostgreSQL engine with pgxpool.
func NewPostgresEngine(ctx context.Context, connString string) (*PostgresEngine, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, eris.Wrapf(err, "db: create pgxpool")
	}

	if err := pool.Ping(ctx); err != nil {
		return nil, eris.Wrapf(err, "db: ping postgres")
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
