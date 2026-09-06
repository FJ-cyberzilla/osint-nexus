package config

import (
	"os"
	"testing"
	"time"
)

func TestLoadConfig_DefaultsAndEnv(t *testing.T) {
	// Override environment variable
	os.Setenv("OSINT_ENGINE_CONCURRENCY", "100")
	defer os.Unsetenv("OSINT_ENGINE_CONCURRENCY")

	cfg, err := LoadConfig("")
	if err != nil {
		t.Fatalf("expected no error loading config, got %v", err)
	}

	if cfg.App.Name != "OSINT-Nexus" {
		t.Errorf("expected App Name 'OSINT-Nexus', got '%s'", cfg.App.Name)
	}

	if cfg.Engine.Concurrency != 100 {
		t.Errorf("expected Concurrency 100 from env, got %d", cfg.Engine.Concurrency)
	}

	if cfg.Engine.TimeoutSeconds != 15*time.Second {
		t.Errorf("expected Timeout 15s, got %v", cfg.Engine.TimeoutSeconds)
	}
}
