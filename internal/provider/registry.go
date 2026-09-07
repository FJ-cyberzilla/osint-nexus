package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// RegistryProvider probes public username registries.
type RegistryProvider struct {
	client *http.Client
}

// NewRegistryProvider initializes a new RegistryProvider.
func NewRegistryProvider() *RegistryProvider {
	return &RegistryProvider{
		client: NewHTTPClient(),
	}
}

// Name returns the provider name.
func (p *RegistryProvider) Name() string {
	return "RegistryProvider"
}

// CheckUsername performs a registry lookup for the given username.
func (p *RegistryProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	// Example registry: https://keybase.io/<username>
	url := fmt.Sprintf("https://keybase.io/%s", username)

	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, fmt.Errorf("provider: registry request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil // User not found
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("provider: registry unexpected status: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := "Registry"
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       "registry-detected",
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: 0.9,
	}, nil
}
