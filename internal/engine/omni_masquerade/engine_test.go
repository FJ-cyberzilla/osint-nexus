package omni_masquerade

import (
	"context"
	"testing"
	"time"
)

func TestNewEngine(t *testing.T) {
	cfg := EngineConfig{
		MaxWorkers: 4,
		Timeout:    10 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	if engine == nil {
		t.Fatal("expected engine instance, got nil")
	}
}

func TestGenerateIntelligenceDatabase(t *testing.T) {
	cfg := EngineConfig{
		MaxWorkers: 4,
		Timeout:    5 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	seed := TargetSeed{
		Username:  "cyber_operative",
		SeedType:  "username",
		Timestamp: time.Now(),
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	db, err := engine.GenerateIntelligenceDatabase(ctx, seed)
	if err != nil {
		t.Fatalf("failed to generate intelligence database: %v", err)
	}

	if db == nil {
		t.Fatal("expected intelligence database result, got nil")
	}

	if db.PrimaryUsername != "cyber_operative" {
		t.Errorf("expected primary username 'cyber_operative', got '%s'", db.PrimaryUsername)
	}

	if len(db.Profiles) == 0 {
		t.Error("expected discovered profiles, got 0")
	}

	if db.GraphNodes == 0 {
		t.Error("expected non-zero graph nodes")
	}
}

func TestGenerateIntelligenceDatabaseEmptySeed(t *testing.T) {
	cfg := EngineConfig{
		MaxWorkers: 2,
		Timeout:    2 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	seed := TargetSeed{
		Username: "",
	}

	ctx := context.Background()
	_, err = engine.GenerateIntelligenceDatabase(ctx, seed)
	if err == nil {
		t.Error("expected error for empty seed username, got nil")
	}
}
