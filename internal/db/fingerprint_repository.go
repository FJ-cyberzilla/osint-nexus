package db

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
)

// FingerprintRepository manages loading and querying fingerprint signatures from disk.
type FingerprintRepository struct {
	dataFilePath string
	data         map[string]map[string]string
	mu           sync.RWMutex
}

// NewFingerprintRepository initializes a new FingerprintRepository with the specified data path.
func NewFingerprintRepository(dataFilePath string) (*FingerprintRepository, error) {
	repo := &FingerprintRepository{
		dataFilePath: dataFilePath,
		data:         make(map[string]map[string]string),
	}
	if err := repo.loadData(); err != nil {
		return nil, fmt.Errorf("fingerprint_repository: load data: %w", err)
	}
	return repo, nil
}

func (r *FingerprintRepository) loadData() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	data, err := os.ReadFile(r.dataFilePath)
	if err != nil {
		// If file doesn't exist, use fallback
		if os.IsNotExist(err) {
			r.data = map[string]map[string]string{
				"ja3": {
					"72a589da586844d7f0818ce684948eea": "Chrome 120 on Windows 10",
					"a0e9f5d64349fb13191bc787f6efad1f": "curl 7.68 on Ubuntu 20.04",
					"e7b6b5f5f5f5f5f5f5f5f5f5f5f5f5":   "Python requests (urllib3)",
				},
			}
			return nil
		}
		return fmt.Errorf("read file: %w", err)
	}

	if err := json.Unmarshal(data, &r.data); err != nil {
		return fmt.Errorf("unmarshal json: %w", err)
	}
	return nil
}

// GetSignature retrieves a signature based on category and hash.
func (r *FingerprintRepository) GetSignature(category, signature string) string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if catData, ok := r.data[category]; ok {
		if val, ok := catData[signature]; ok {
			return val
		}
	}
	return "unknown"
}
