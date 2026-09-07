package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// AparatProvider probes the Aparat video platform.
type AparatProvider struct {
	client *http.Client
}

// NewAparatProvider initializes a new AparatProvider.
func NewAparatProvider() *AparatProvider {
	return &AparatProvider{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// Name returns the provider name.
func (p *AparatProvider) Name() string {
	return "Aparat"
}

// CheckUsername probes Aparat for the username.
func (p *AparatProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.aparat.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("aparat: create request: %w", err)
	}

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("aparat: execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Aparat"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{
				{
					Username: &username,
					Platform: &platform,
				},
			},
			ConfidenceScore: 0.8,
		}, nil
	}
	return nil, nil // Username not found or error
}
