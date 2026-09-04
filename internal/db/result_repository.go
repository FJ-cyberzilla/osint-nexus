package db

import (
	"fmt"
	"github.com/osint-nexus/internal/types"
)

// ResultRepository handles CRUD operations for scan results.
type ResultRepository struct {
	engine *SQLiteEngine
}

// NewResultRepository initializes a new ResultRepository.
func NewResultRepository(engine *SQLiteEngine) *ResultRepository {
	return &ResultRepository{engine: engine}
}

// Save inserts a new scan result.
func (r *ResultRepository) Save(username, platform string, found bool) error {
	foundInt := 0
	if found {
		foundInt = 1
	}
	query := "INSERT INTO results (username, platform, found) VALUES (?, ?, ?)"
	return r.engine.Exec(query, username, platform, foundInt)
}

// SaveBatch inserts multiple scan results in a single transaction.
func (r *ResultRepository) SaveBatch(query string, data ...[]interface{}) error {
	return r.engine.ExecMany(query, data...)
}

// Query retrieves scan results based on filters.
func (r *ResultRepository) Query(username, platform string, limit int) ([]types.ScanResult, error) {
	query := "SELECT id, username, platform, found, timestamp FROM results WHERE 1=1"
	var params []interface{}

	if username != "" {
		query += " AND username = ?"
		params = append(params, username)
	}
	if platform != "" {
		query += " AND platform = ?"
		params = append(params, platform)
	}
	query += " ORDER BY timestamp DESC LIMIT ?"
	params = append(params, limit)

	rows, err := r.engine.DB().Query(query, params...)
	if err != nil {
		return nil, fmt.Errorf("db: query: %w", err)
	}
	defer rows.Close()

	var results []types.ScanResult
	for rows.Next() {
		var res types.ScanResult
		var foundInt int
		if err := rows.Scan(&res.ID, &res.Username, &res.Platform, &foundInt, &res.Timestamp); err != nil {
			return nil, fmt.Errorf("db: scan: %w", err)
		}
		res.Found = (foundInt == 1)
		results = append(results, res)
	}
	return results, nil
}
