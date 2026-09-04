package db

import (
	"os"
	"testing"
)

func TestResultRepository(t *testing.T) {
	dbPath := "test_repo.sqlite"
	defer os.Remove(dbPath)

	engine, err := NewSQLiteEngine(dbPath)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}
	defer engine.Close()

	err = engine.Exec("CREATE TABLE results (id INTEGER PRIMARY KEY, username TEXT, platform TEXT, found INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
	if err != nil {
		t.Fatalf("failed to create table: %v", err)
	}

	repo := NewResultRepository(engine)

	err = repo.Save("user1", "twitter", true)
	if err != nil {
		t.Fatalf("failed to save: %v", err)
	}

	results, err := repo.Query("user1", "twitter", 1)
	if err != nil {
		t.Fatalf("failed to query: %v", err)
	}

	if len(results) != 1 {
		t.Errorf("expected 1 result, got %d", len(results))
	}
}
