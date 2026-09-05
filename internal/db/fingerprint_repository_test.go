package db

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestFingerprintRepository_New(t *testing.T) {
	// Setup: Create a temporary valid JSON file
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, "fingerprints.json")
	data := map[string]map[string]string{
		"ja3": {
			"test-hash": "test-signature",
		},
	}
	jsonData, _ := json.Marshal(data)
	err := os.WriteFile(filePath, jsonData, 0644)
	if err != nil {
		t.Fatalf("Failed to create temporary file: %v", err)
	}

	// Test case: Load valid file
	repo, err := NewFingerprintRepository(filePath)
	if err != nil {
		t.Errorf("NewFingerprintRepository failed with valid file: %v", err)
	}
	if repo == nil {
		t.Error("Expected repository, got nil")
	}
}

func TestFingerprintRepository_LoadData_Fallback(t *testing.T) {
	// Test case: Load non-existent file (trigger fallback)
	repo, err := NewFingerprintRepository("non-existent.json")
	if err != nil {
		t.Errorf("NewFingerprintRepository failed with non-existent file: %v", err)
	}

	// Check fallback data
	sig := repo.GetSignature("ja3", "72a589da586844d7f0818ce684948eea")
	if sig != "Chrome 120 on Windows 10" {
		t.Errorf("Expected Chrome 120, got %s", sig)
	}
}

func TestFingerprintRepository_LoadData_InvalidJSON(t *testing.T) {
	// Setup: Create a temporary invalid JSON file
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, "invalid.json")
	err := os.WriteFile(filePath, []byte("{invalid-json"), 0644)
	if err != nil {
		t.Fatalf("Failed to create invalid file: %v", err)
	}

	// Test case: Should fail loading
	_, err = NewFingerprintRepository(filePath)
	if err == nil {
		t.Error("Expected error loading invalid JSON, got nil")
	}
}

func TestFingerprintRepository_GetSignature(t *testing.T) {
	// Setup: Use fallback data
	repo, _ := NewFingerprintRepository("non-existent.json")

	tests := []struct {
		name      string
		category  string
		signature string
		expected  string
	}{
		{"Valid", "ja3", "72a589da586844d7f0818ce684948eea", "Chrome 120 on Windows 10"},
		{"UnknownCategory", "unknown", "hash", "unknown"},
		{"UnknownSignature", "ja3", "unknown-hash", "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := repo.GetSignature(tt.category, tt.signature)
			if got != tt.expected {
				t.Errorf("GetSignature() = %v, want %v", got, tt.expected)
			}
		})
	}
}
