package provider

import (
	"sync"

	"github.com/osint-nexus/internal/types"
)

var (
	providers []types.Provider
	mu        sync.RWMutex
)

// Register adds a provider to the global registry.
func Register(p types.Provider) {
	mu.Lock()
	defer mu.Unlock()
	providers = append(providers, p)
}

// GetProviders returns all registered providers.
func GetProviders() []types.Provider {
	mu.RLock()
	defer mu.RUnlock()
	// Return a copy to prevent external modification
	cp := make([]types.Provider, len(providers))
	copy(cp, providers)
	return cp
}
