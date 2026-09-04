package db

import (
	"os"
	"testing"
)

func TestSQLiteEngine(t *testing.T) {
	dbPath := "test.sqlite"
	defer os.Remove(dbPath)

	engine, err := NewSQLiteEngine(dbPath)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}
	defer engine.Close()

	err = engine.Exec("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
	if err != nil {
		t.Fatalf("failed to create table: %v", err)
	}

	err = engine.Exec("INSERT INTO test (name) VALUES (?)", "test_item")
	if err != nil {
		t.Fatalf("failed to insert: %v", err)
	}

	var name string
	err = engine.QueryRow("SELECT name FROM test WHERE id = ?", 1).Scan(&name)
	if err != nil {
		t.Fatalf("failed to select: %v", err)
	}

	if name != "test_item" {
		t.Errorf("expected test_item, got %s", name)
	}
}
