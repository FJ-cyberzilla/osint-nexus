package omni_masquerade

import (
	"context"
	"os"
	"path/filepath"
	"sync"

	"github.com/rotisserie/eris"
)

// TempManager handles ephemeral session scratchpads, cache files, and temporary browser profile directories.
type TempManager struct {
	baseDir string
	mu      sync.Mutex
	files   map[string]string
}

// NewTempManager initializes a new TempManager within the specified temporary workspace.
func NewTempManager(baseDir string) (*TempManager, error) {
	if baseDir == "" {
		baseDir = filepath.Join(os.TempDir(), "osint_nexus_omni_temp")
	}

	if err := os.MkdirAll(baseDir, 0700); err != nil {
		return nil, eris.Wrapf(err, "temp_manager: create base directory %s", baseDir)
	}

	return &TempManager{
		baseDir: baseDir,
		files:   make(map[string]string),
	}, nil
}

// CreateScratchFile creates a temporary scratch file with the given prefix and content.
func (tm *TempManager) CreateScratchFile(ctx context.Context, prefix string, content []byte) (string, error) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	tmpFile, err := os.CreateTemp(tm.baseDir, prefix+"_*.tmp")
	if err != nil {
		return "", eris.Wrap(err, "temp_manager: create temp file")
	}
	defer tmpFile.Close()

	if _, err := tmpFile.Write(content); err != nil {
		return "", eris.Wrap(err, "temp_manager: write temp file")
	}

	path := tmpFile.Name()
	tm.files[path] = path
	return path, nil
}

// Cleanup purges all tracked temporary scratch files and directories.
func (tm *TempManager) Cleanup() error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	var firstErr error
	for path := range tm.files {
		if err := os.Remove(path); err != nil && !os.IsNotExist(err) && firstErr == nil {
			firstErr = eris.Wrapf(err, "temp_manager: remove temp file %s", path)
		}
		delete(tm.files, path)
	}

	return firstErr
}
