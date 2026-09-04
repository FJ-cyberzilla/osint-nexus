package db

import (
	"database/sql"
	"fmt"

	_ "github.com/mattn/go-sqlite3"
)

// SQLiteEngine implements the database engine using SQLite.
type SQLiteEngine struct {
	dbPath string
	db     *sql.DB
}

// NewSQLiteEngine initializes a new SQLite engine with WAL mode and foreign keys enabled.
func NewSQLiteEngine(dbPath string) (*SQLiteEngine, error) {
	// Use WAL mode for better concurrency and enable foreign keys.
	dsn := fmt.Sprintf("%s?_journal_mode=WAL&_foreign_keys=ON", dbPath)
	db, err := sql.Open("sqlite3", dsn)
	if err != nil {
		return nil, fmt.Errorf("db: open sqlite: %w", err)
	}

	// Configure connection pool for SQLite. 
	// SQLite supports only one writer at a time, so 1 max open connection is safe.
	db.SetMaxOpenConns(1)

	return &SQLiteEngine{
		dbPath: dbPath,
		db:     db,
	}, nil
}

// Exec executes a query without returning any rows.
func (e *SQLiteEngine) Exec(query string, args ...interface{}) error {
	_, err := e.db.Exec(query, args...)
	if err != nil {
		return fmt.Errorf("db: exec: %w", err)
	}
	return nil
}

// ExecMany executes a query multiple times with different sets of arguments.
func (e *SQLiteEngine) ExecMany(query string, argsList ...[]interface{}) error {
	tx, err := e.db.Begin()
	if err != nil {
		return fmt.Errorf("db: begin tx: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(query)
	if err != nil {
		return fmt.Errorf("db: prepare: %w", err)
	}
	defer stmt.Close()

	for _, args := range argsList {
		_, err := stmt.Exec(args...)
		if err != nil {
			return fmt.Errorf("db: exec many: %w", err)
		}
	}

	return tx.Commit()
}

// QueryRow executes a query that is expected to return at most one row.
func (e *SQLiteEngine) QueryRow(query string, args ...interface{}) *sql.Row {
	return e.db.QueryRow(query, args...)
}

// QueryAll executes a query and returns all rows as a slice of maps.
func (e *SQLiteEngine) QueryAll(query string, args ...interface{}) ([]map[string]interface{}, error) {
	rows, err := e.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("db: query: %w", err)
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		return nil, fmt.Errorf("db: columns: %w", err)
	}

	var results []map[string]interface{}
	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range values {
			valuePtrs[i] = &values[i]
		}
		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, fmt.Errorf("db: scan: %w", err)
		}
		row := make(map[string]interface{})
		for i, col := range columns {
			row[col] = values[i]
		}
		results = append(results, row)
	}
	return results, nil
}

// Close closes the database connection.
func (e *SQLiteEngine) Close() error {
	return e.db.Close()
}

// DB returns the underlying sql.DB instance.
func (e *SQLiteEngine) DB() *sql.DB {
	return e.db
}

// EnsureSchema initializes the database schema if it doesn't exist.
func (e *SQLiteEngine) EnsureSchema() error {
	query := `
	CREATE TABLE IF NOT EXISTS results (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT NOT NULL,
		platform TEXT NOT NULL,
		found INTEGER NOT NULL,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);`
	return e.Exec(query)
}
